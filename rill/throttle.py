"""The token bucket: burst is allowed, sustained excess is not, per key.

A stream shared by many tenants needs per-key rate limits,
and the token bucket is the shape that matches how traffic
actually behaves: each key holds a bucket that refills at the
sustained rate and caps at the burst size, an event spends a
token or waits, so a quiet key can burst its full bucket at
once while a loud key settles to exactly the refill rate,
which is the whole point, bursts are legitimate and sustained
excess is not. The refusal carries the retry arithmetic, when
the next token lands, because a 429 without a retry-after
teaches clients to hammer. The fairness meter is the part
multi-tenant systems skip: it reports tokens spent per key
against the fleet, so the tenant consuming half the shared
capacity is a line item before the other tenants' latency
becomes the evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class TokenBucket:
    refill_per_tick: int
    burst: int
    tokens: dict[str, int] = field(default_factory=dict)
    last_seen: dict[str, int] = field(default_factory=dict)
    spent: dict[str, int] = field(default_factory=dict)
    refusals: int = 0

    def __post_init__(self) -> None:
        if self.refill_per_tick < 1 or self.burst < 1:
            raise Invalid(
                "the bucket needs a refill rate and a burst "
                "size, both positive"
            )
        if self.burst < self.refill_per_tick:
            raise Invalid(
                "a burst below the refill rate throttles "
                "steady traffic; that is a smaller bucket than "
                "the tap"
            )

    def _refill(self, key: str, now: int) -> None:
        last = self.last_seen.get(key)
        held = self.tokens.get(key, self.burst)
        if last is not None and now > last:
            held = min(
                self.burst,
                held + (now - last) * self.refill_per_tick,
            )
        self.tokens[key] = held
        self.last_seen[key] = now

    def admit(self, key: str, now: int) -> tuple[bool, str]:
        if not key:
            raise Invalid("rate limits are per key")
        self._refill(key, now)
        if self.tokens[key] >= 1:
            self.tokens[key] -= 1
            self.spent[key] = self.spent.get(key, 0) + 1
            return True, f"{key}: token spent, {self.tokens[key]} left"
        self.refusals += 1
        wait = -(-1 // self.refill_per_tick)
        return False, (
            f"{key}: throttled, next token in {wait} tick(s); "
            "a refusal without retry arithmetic teaches "
            "clients to hammer"
        )

    def fairness_meter(self) -> str:
        total = sum(self.spent.values())
        if total == 0:
            raise Invalid("nobody has spent a token")
        hog = max(self.spent, key=lambda key: self.spent[key])
        share = 100 * self.spent[hog] // total
        line = (
            f"{total} token(s) spent across "
            f"{len(self.spent)} key(s); {hog} holds {share}%"
        )
        if share >= 50 and len(self.spent) > 1:
            line += (
                ": a line item before the other tenants' "
                "latency becomes the evidence"
            )
        return line

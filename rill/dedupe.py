"""Deduplication: the third setting on the dial, bought with memory.

At-least-once delivery plus idempotence equals effectively
once, and idempotence here is a remembered set: each event
carries an identity, the deduper admits an identity the first
time and refuses the replay, and exactly-once emerges not
from the transport but from the memory. The memory is the
whole price, and the deduper pays it honestly with a bounded
horizon: identities older than the horizon are forgotten, so
a replay arriving later than the horizon slips through, and
the module says so in its contract rather than its
postmortem, because "exactly once, within a horizon we can
afford" is the true product and every vendor slide that omits
the second clause is selling the first word twice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Deduper:
    horizon: int
    seen: dict[str, int] = field(default_factory=dict)
    admitted: int = 0
    refused: int = 0
    slipped_estimate: int = 0

    def __post_init__(self) -> None:
        if self.horizon <= 0:
            raise Invalid(
                "a horizon of zero remembers nothing and "
                "dedupes nothing"
            )

    def offer(self, identity: str, now: int) -> bool:
        if not identity:
            raise Invalid("an event without identity cannot repeat")
        last = self.seen.get(identity)
        if last is not None and now - last <= self.horizon:
            self.refused += 1
            return False
        if last is not None:
            self.slipped_estimate += 1
        self.seen[identity] = now
        self.admitted += 1
        return True

    def forget_old(self, now: int) -> int:
        doomed = [
            identity
            for identity, last in self.seen.items()
            if now - last > self.horizon
        ]
        for identity in doomed:
            del self.seen[identity]
        return len(doomed)

    def contract(self) -> str:
        return (
            f"exactly once, within a horizon of "
            f"{self.horizon}: {self.admitted} admitted, "
            f"{self.refused} replay(s) refused, "
            f"{self.slipped_estimate} known slip(s) past the "
            "horizon; the second clause is the honest half of "
            "the product"
        )

"""Rate limiting a stream source: the token bucket that smooths without dropping.

An upstream that bursts faster than the pipeline can absorb
needs limiting, and the naive limiter, drop everything above a
fixed rate, punishes a brief legitimate burst the same as a
sustained flood. The token bucket does better: tokens refill
at a steady rate up to a burst capacity, each event spends a
token, and a short burst draws down the accumulated tokens
and is admitted while a sustained overload runs the bucket dry
and is throttled. The capacity is the burst tolerance and the
refill rate is the sustained ceiling, two separate knobs for
two separate concerns, and conflating them, the fixed-rate
limiter's flaw, means choosing between dropping bursts and
allowing floods. The module meters admitted against throttled
and reports the burst headroom used, because a bucket that
never draws below full is oversized and one that is always
empty is undersized, and the draw-down distribution is the
only thing that says which.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class TokenBucket:
    capacity: int
    refill_per_tick: int
    tokens: float = 0.0
    last_refill: int = 0
    admitted: int = 0
    throttled: int = 0
    min_tokens_seen: float = 0.0

    def __post_init__(self) -> None:
        if self.capacity < 1 or self.refill_per_tick < 1:
            raise Invalid(
                "the bucket needs positive capacity and refill"
            )
        self.tokens = float(self.capacity)
        self.min_tokens_seen = float(self.capacity)

    def _refill(self, now: int) -> None:
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_per_tick,
        )
        self.last_refill = now

    def admit(self, now: int) -> str:
        self._refill(now)
        if self.tokens >= 1:
            self.tokens -= 1
            self.admitted += 1
            self.min_tokens_seen = min(
                self.min_tokens_seen, self.tokens
            )
            return f"admitted, {self.tokens:.0f} token(s) left"
        self.throttled += 1
        return (
            "throttled: bucket dry, a sustained overload not a "
            "brief burst"
        )

    def headroom_report(self) -> str:
        total = self.admitted + self.throttled
        if total == 0:
            raise Invalid("nothing offered")
        used = self.capacity - self.min_tokens_seen
        share = 100 * used / self.capacity
        if self.min_tokens_seen >= self.capacity * 0.9:
            sizing = "oversized: the burst headroom went unused"
        elif self.throttled > 0:
            sizing = "undersized: the bucket ran dry and threw work"
        else:
            sizing = "well-sized: bursts absorbed, none dropped"
        return (
            f"{self.admitted} admitted, {self.throttled} "
            f"throttled, burst headroom used {share:.0f}%; "
            f"{sizing}"
        )

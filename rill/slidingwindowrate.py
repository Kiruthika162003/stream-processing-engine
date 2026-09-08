"""Rate limiting windows: the fixed window leaks a double burst at its own seam.

A fixed-window rate limiter counts requests per aligned window,
a minute say, and resets the count at each boundary, which is
cheap and wrong at exactly one place: the seam. Fill the limit in
the last instant of one window and fill it again in the first
instant of the next, and twice the limit has passed within a span
shorter than a single window, because the counter saw two windows
each within budget and never saw the span that straddled them. A
sliding-window log fixes it by keeping the timestamps and
counting only those inside the trailing window from now, so the
straddling span is counted as one and the limit holds over every
window-length interval, not just the aligned ones. The log costs
memory proportional to the limit, which is the price of exactness
and the reason the cheaper fixed window survives despite its
seam. This module runs both against the same boundary-straddling
traffic so the leak is a measurement: the fixed window admits
twice its limit across the seam that the sliding log refuses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class FixedWindowLimiter:
    limit: int
    window: int
    _counts: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.limit <= 0 or self.window <= 0:
            raise Invalid("limit and window must be positive")

    def allow(self, now: int) -> bool:
        bucket = now // self.window
        if self._counts.get(bucket, 0) >= self.limit:
            return False
        self._counts[bucket] = self._counts.get(bucket, 0) + 1
        return True


@dataclass
class SlidingLogLimiter:
    limit: int
    window: int
    _stamps: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.limit <= 0 or self.window <= 0:
            raise Invalid("limit and window must be positive")

    def allow(self, now: int) -> bool:
        cutoff = now - self.window
        self._stamps = [t for t in self._stamps if t > cutoff]
        if len(self._stamps) >= self.limit:
            return False
        self._stamps.append(now)
        return True

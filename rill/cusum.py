"""CUSUM: catching a small sustained shift a per-point threshold never trips.

Watching a stream's mean for a change splits into two failure
modes a naive threshold handles badly. A big spike it catches, but
a small persistent shift, the mean creeping from zero to plus one
when the noise is several times that, never crosses a per-point
band, so a threshold test stares straight at a drifted process and
calls every sample normal. The cumulative sum control chart
catches exactly that. It accumulates each sample's deviation from
the target, minus a slack that absorbs ordinary noise, into a
running sum floored at zero, so isolated noise cancels out and
never builds, but a shift that pushes the samples consistently to
one side makes the sum climb without resetting until it crosses an
alarm threshold. The detection is not instant, it takes enough
post-shift samples for the sum to accumulate past the threshold,
which is the price of sensitivity to a change too small to see in
any single reading. Two sums run, one for upward shifts and one
for downward, so a drift in either direction is caught. This
module runs both sums and alarms when either crosses, so the
detection of a shift smaller than the noise is a measured event
rather than a claim about control charts.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class Cusum:
    target: float
    slack: float
    threshold: float
    _high: float = 0.0
    _low: float = 0.0

    def __post_init__(self) -> None:
        if self.slack < 0 or self.threshold <= 0:
            raise Invalid("slack non-negative and threshold positive")

    def update(self, sample: float) -> str | None:
        self._high = max(0.0, self._high + (sample - self.target - self.slack))
        self._low = max(0.0, self._low + (self.target - self.slack - sample))
        if self._high > self.threshold:
            return "up"
        if self._low > self.threshold:
            return "down"
        return None

    def reset(self) -> None:
        self._high = 0.0
        self._low = 0.0

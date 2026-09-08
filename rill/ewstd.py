"""EW standard deviation: an anomaly band that widens in noise and tightens in calm.

Flagging a value as anomalous by whether it sits more than a few
standard deviations from the mean needs both a mean and a spread,
and on a stream both should track the recent past rather than the
whole history, because a process that was calm and is now volatile
should be judged by its current volatility, not its lifetime one.
An exponentially weighted mean and variance give exactly that. The
mean is the usual decayed blend of values, and the variance is a
decayed blend of the squared deviations from that mean, so both
forget the distant past at the same rate. An anomaly band is then
the mean plus or minus some multiple of the square root of the
variance, and because the variance breathes with the recent
spread, the band widens during a noisy stretch so ordinary
volatility does not trip it, and tightens during a calm one so a
small genuine excursion still stands out. A fixed band cannot do
both: set wide enough for the noisy period it misses the calm
period's anomalies, set tight for the calm period it screams all
through the noisy one. This module tracks the exponentially
weighted mean and variance and reports whether a value falls
outside the adaptive band, so the band that follows the volatility
is a measured behavior rather than a tuned constant.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class EwStdDev:
    alpha: float
    _mean: float | None = None
    _variance: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha <= 1.0:
            raise Invalid("alpha must be in (0, 1]")

    def update(self, value: float) -> None:
        if self._mean is None:
            self._mean = value
            return
        delta = value - self._mean
        self._mean += self.alpha * delta
        self._variance = (1 - self.alpha) * (self._variance + self.alpha * delta * delta)

    def mean(self) -> float:
        if self._mean is None:
            raise Invalid("no observations yet")
        return self._mean

    def stddev(self) -> float:
        return math.sqrt(self._variance)

    def is_anomaly(self, value: float, sigmas: float = 3.0) -> bool:
        if self._mean is None:
            raise Invalid("no observations yet")
        return abs(value - self._mean) > sigmas * self.stddev()

"""Rate-based breaker: tripping on a failure fraction the consecutive-count breaker never sees.

A circuit breaker that trips after so many failures in a row
misses the failure mode that hurts most in practice: intermittent
failure. A dependency that fails half its calls, but never several
in a row because a success always sneaks between, keeps a
consecutive-count breaker's counter resetting to zero, so the
breaker stays closed while half the traffic errors, which is
plainly a broken dependency the breaker was supposed to catch. A
rolling-window rate breaker watches the fraction of failures over
the last so-many calls instead of the streak, and trips when that
fraction crosses a threshold, so a steady fifty-percent failure
rate opens the breaker even though it never produces a run of
failures. The window is the memory: it must be long enough to
estimate the rate without noise from a handful of calls, and a
minimum sample count guards against tripping on the first unlucky
call before the window has filled. The trade against the
consecutive breaker is that the rate breaker reacts a little
slower, needing a window's worth of calls to be sure, in exchange
for catching the intermittent failures the streak counter is
blind to. This module keeps a sliding window of outcomes and trips
on the failure fraction, so the intermittent failure a streak
breaker sleeps through is a measured trip.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class RateBreaker:
    window: int
    threshold: float
    min_samples: int = 1
    _outcomes: deque[bool] = field(default_factory=deque)

    def __post_init__(self) -> None:
        if self.window < 1:
            raise Invalid("window must be positive")
        if not 0.0 < self.threshold <= 1.0:
            raise Invalid("threshold is a fraction in (0, 1]")

    def record(self, success: bool) -> None:
        self._outcomes.append(success)
        while len(self._outcomes) > self.window:
            self._outcomes.popleft()

    def failure_rate(self) -> float:
        if not self._outcomes:
            return 0.0
        failures = sum(1 for ok in self._outcomes if not ok)
        return failures / len(self._outcomes)

    def tripped(self) -> bool:
        if len(self._outcomes) < self.min_samples:
            return False
        return self.failure_rate() > self.threshold

"""Phi-accrual failure detection: a suspicion level, not a hair-trigger timeout.

A fixed heartbeat timeout is a coin flip at the boundary: one
interval late and the node is declared dead, even if that node
has always been a little irregular and is merely slow this
second. The phi-accrual detector replaces the yes-or-no with a
number. It watches the inter-arrival times of past heartbeats,
learns their mean and spread, and for the current silence
computes phi, the negative log of the probability that a
heartbeat this late has still not been a real failure. A gap that
is ordinary for this node yields a low phi and no alarm; a gap
far out on the tail of what this node normally does yields a high
phi. The payoff is that the same absolute silence means different
things for different nodes: for a node whose heartbeats are
tightly regular a three-times-normal gap is deeply suspicious,
while for a node that has always been erratic the same gap is
within its habits and barely moves phi, so the erratic node is
not falsely accused the way a fixed timeout would accuse it. This
module accumulates the intervals, estimates the distribution, and
reports phi and a thresholded suspicion, so adaptivity is a
measured value rather than a tuning knob nobody dares touch.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class PhiAccrual:
    min_std: float = 1.0
    _intervals: list[float] = field(default_factory=list)
    _last_beat: float | None = None

    def heartbeat(self, now: float) -> None:
        if self._last_beat is not None:
            interval = now - self._last_beat
            if interval < 0:
                raise Invalid("heartbeat went backward in time")
            self._intervals.append(interval)
        self._last_beat = now

    def _distribution(self) -> tuple[float, float]:
        if len(self._intervals) < 2:
            raise Invalid("need at least two heartbeats to estimate the interval")
        mean = statistics.fmean(self._intervals)
        std = max(self.min_std, statistics.pstdev(self._intervals))
        return mean, std

    def phi(self, now: float) -> float:
        if self._last_beat is None:
            raise Invalid("no heartbeat seen yet")
        mean, std = self._distribution()
        gap = now - self._last_beat
        z = (gap - mean) / std
        survival = 0.5 * math.erfc(z / math.sqrt(2))
        survival = min(max(survival, 1e-12), 1.0)
        return -math.log10(survival)

    def suspect(self, now: float, threshold: float) -> bool:
        return self.phi(now) >= threshold

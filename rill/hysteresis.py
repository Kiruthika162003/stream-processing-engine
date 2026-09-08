"""Hysteresis watermarks: two thresholds so a full buffer stops flapping the producer.

A bounded buffer that backpressures its producer needs to decide
when to pause it and when to let it resume, and doing both at a
single threshold is a mistake that shows up as chatter. If the
producer pauses the instant the buffer crosses a level and resumes
the instant it drops back below, then a buffer hovering right at
that level flips the producer pause-resume-pause-resume on every
single push and pop, a storm of control signals that costs more
than the backpressure it implements. Hysteresis fixes it with two
levels instead of one: pause the producer when the buffer fills to
a high watermark, and resume it only when the buffer drains all
the way down to a lower low watermark, so between the two the
state is sticky and a small oscillation cannot cross both. The gap
between the watermarks is the damping, wide enough that ordinary
jitter stays inside it and only a real trend moves the state. The
same shape governs thermostats and Schmitt triggers for the same
reason: a single setpoint chatters, a band holds. This module runs
the buffer with a high and a low watermark and reports the paused
state and how many times it flipped, so the flapping a single
threshold causes and the calm two thresholds give are a measured
count.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class HysteresisBuffer:
    low: int
    high: int
    _depth: int = 0
    _paused: bool = False
    _flips: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.low < self.high:
            raise Invalid("need 0 <= low < high")

    def _update(self) -> None:
        was = self._paused
        if self._depth >= self.high:
            self._paused = True
        elif self._depth <= self.low:
            self._paused = False
        if self._paused != was:
            self._flips += 1

    def push(self, count: int = 1) -> None:
        if count < 0:
            raise Invalid("count cannot be negative")
        self._depth += count
        self._update()

    def pop(self, count: int = 1) -> None:
        if count < 0:
            raise Invalid("count cannot be negative")
        self._depth = max(0, self._depth - count)
        self._update()

    def paused(self) -> bool:
        return self._paused

    def flips(self) -> int:
        return self._flips

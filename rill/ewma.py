"""EWMA: an exponential moving average that reads low until you correct its warm-up.

An exponential moving average smooths a noisy signal by blending
each new sample with the running estimate, weighted by a factor
alpha, so it tracks the signal while filtering the jitter. Started
from zero, though, it lies at the beginning. The first estimate
is only alpha of the first sample, a fraction of the truth,
because the average is still mostly the zero it was seeded with,
and it takes many samples for that seed to decay out, so early
readings systematically under-report a signal that is actually
steady. This is not noise, it is a bias with a known size: after
t updates the estimate carries a leftover of the seed weighing
one minus alpha to the t. Dividing the estimate by one minus that
same factor cancels the seed's remaining weight exactly, so the
bias-corrected average reads the true level from the very first
sample instead of crawling up to it, the same correction Adam
uses on its moment estimates. This module keeps the raw average
and the corrected one, so the warm-up bias and its removal are a
measured pair: on a constant input the raw value creeps up while
the corrected value is right immediately.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class Ewma:
    alpha: float
    _value: float = 0.0
    _steps: int = 0

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha <= 1.0:
            raise Invalid("alpha must be in (0, 1]")

    def update(self, sample: float) -> None:
        self._value = self.alpha * sample + (1 - self.alpha) * self._value
        self._steps += 1

    def raw(self) -> float:
        return self._value

    def corrected(self) -> float:
        if self._steps == 0:
            raise Invalid("no samples yet")
        bias = 1 - (1 - self.alpha) ** self._steps
        return self._value / bias

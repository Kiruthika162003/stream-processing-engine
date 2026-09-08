"""Frugal streaming median: estimating the middle with a single number and a step.

Estimating a stream's median usually keeps a summary of many
samples, and the frugal-1U algorithm asks how little memory that
really takes: one number. It holds a single estimate and, for each
sample, nudges the estimate up by a step when the sample is above
it and down by a step when the sample is below it. At the true
median, half the samples fall on each side, so the up-nudges and
down-nudges balance and the estimate stops drifting, hovering
around the median; below the median more samples are above the
estimate so it is pushed up, and above the median it is pushed
down, so it is drawn to the middle from either side. The estimate
never converges to a fixed point, it random-walks in a tight band
around the median whose width is the step, so a large step chases
a moving median quickly but sits noisier, and a small step is
steadier but slower to follow a shift, the familiar
responsiveness-for-stability trade in yet another guise. The
astonishing part is that a single stored value, no histogram and
no sample buffer, tracks the median of an unbounded stream at all.
This module runs the one-number estimator, so the convergence to
the median from a single unit of memory is a measured landing
rather than a claim about frugality.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class FrugalMedian:
    step: int = 1
    _estimate: float = 0.0
    _seen: int = 0

    def __post_init__(self) -> None:
        if self.step <= 0:
            raise Invalid("step must be positive")

    def update(self, sample: float) -> None:
        if self._seen == 0:
            self._estimate = sample
        elif sample > self._estimate:
            self._estimate += self.step
        elif sample < self._estimate:
            self._estimate -= self.step
        self._seen += 1

    def median(self) -> float:
        if self._seen == 0:
            raise Invalid("no samples yet")
        return self._estimate

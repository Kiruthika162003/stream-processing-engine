"""Welford's variance: one pass, stable, where the textbook formula cancels itself to junk.

Variance is often computed the way the textbook writes it, the
mean of the squares minus the square of the mean, which needs
only two running sums and one pass. It also destroys itself on
the data that matters. When the values are large and their spread
is small, sensor readings clustered around a billion, timestamps
near an epoch, the mean of the squares and the square of the mean
are two enormous nearly-equal numbers, and subtracting them in
floating point cancels almost every significant digit, leaving a
variance that is wildly wrong and sometimes negative, which is
impossible and a dead giveaway. Welford's method avoids the
catastrophe by never forming those huge sums. It keeps a running
mean and a running sum of squared deviations from that mean,
updating both with each sample using the deviation before and
after the mean shifts, so every quantity it holds stays on the
scale of the spread rather than the scale of the values. It is
still one pass and constant memory, and it is accurate on exactly
the large-offset small-spread inputs the naive formula ruins.
This module runs Welford and, for contrast, the naive formula, so
the cancellation is a measured wrong answer beside a right one.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class Welford:
    _count: int = 0
    _mean: float = 0.0
    _m2: float = 0.0

    def update(self, sample: float) -> None:
        self._count += 1
        delta = sample - self._mean
        self._mean += delta / self._count
        delta2 = sample - self._mean
        self._m2 += delta * delta2

    def mean(self) -> float:
        if self._count == 0:
            raise Invalid("no samples yet")
        return self._mean

    def variance(self) -> float:
        if self._count == 0:
            raise Invalid("no samples yet")
        return self._m2 / self._count


def naive_variance(samples: list[float]) -> float:
    if not samples:
        raise Invalid("no samples")
    count = len(samples)
    mean_of_squares = sum(x * x for x in samples) / count
    square_of_mean = (sum(samples) / count) ** 2
    return mean_of_squares - square_of_mean

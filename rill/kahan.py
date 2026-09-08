"""Kahan summation: keeping the low-order bits a long running float sum keeps dropping.

Adding a long stream of floating-point numbers loses accuracy in
a way that is invisible per step and large in aggregate. Each
addition rounds the result to fit the mantissa, discarding the
low-order bits that did not fit, and over millions of additions
those discarded bits accumulate into a real error, so a running
sum of many small values drifts away from the truth even though
no single addition looked wrong. Kahan summation recovers the
lost bits with a compensation term. After each addition it
computes exactly how much was rounded away, by subtracting the
old sum and the added value back out, and carries that residual
into the next addition so the bits that would have been lost are
folded back in. The running sum stays accurate across a stream
far longer than the naive one, at the cost of a few extra
operations per element and one extra float of state. This module
keeps the compensated sum and, for contrast, the naive one, so
the drift is a measured gap on a sum long enough for the naive
version to visibly lose its footing.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class KahanSum:
    _sum: float = 0.0
    _compensation: float = 0.0

    def add(self, value: float) -> None:
        adjusted = value - self._compensation
        total = self._sum + adjusted
        self._compensation = (total - self._sum) - adjusted
        self._sum = total

    def total(self) -> float:
        return self._sum


def naive_sum(values: list[float]) -> float:
    if not values:
        raise Invalid("no values to sum")
    total = 0.0
    for value in values:
        total += value
    return total

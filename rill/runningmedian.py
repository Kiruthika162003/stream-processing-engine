"""Running median: two heaps holding the halves, so the middle is always at the tops.

Keeping the exact median of a growing stream needs the middle
element on demand, and re-sorting on every insert is quadratic
over the stream. Two heaps keep the median at their fingertips. A
max-heap holds the smaller half of the values seen and a min-heap
holds the larger half, balanced so their sizes differ by at most
one, and because the max-heap's top is the largest of the small
half and the min-heap's top is the smallest of the large half, the
median is right there: the top of the larger heap when the counts
are unequal, or the average of the two tops when they are equal.
Inserting a value pushes it onto the correct half and then
rebalances by moving one element across if a half grew too big,
each step a logarithmic heap operation, so the whole stream costs
n log n and the median is available in constant time after each
insert. This is the exact counterpart to the frugal estimator's
single approximate number: the two heaps pay logarithmic time and
linear memory to know the median precisely, where frugal pays
constant time and one value to know it roughly, and which you want
depends on whether the stream fits in memory. This module keeps
the two heaps balanced and reports the exact running median,
checked against a full sort.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class RunningMedian:
    _lower: list[int] = field(default_factory=list)
    _upper: list[int] = field(default_factory=list)

    def add(self, value: int) -> None:
        if not self._lower or value <= -self._lower[0]:
            heapq.heappush(self._lower, -value)
        else:
            heapq.heappush(self._upper, value)
        if len(self._lower) > len(self._upper) + 1:
            heapq.heappush(self._upper, -heapq.heappop(self._lower))
        elif len(self._upper) > len(self._lower):
            heapq.heappush(self._lower, -heapq.heappop(self._upper))

    def median(self) -> float:
        if not self._lower:
            raise Invalid("no values yet")
        if len(self._lower) > len(self._upper):
            return float(-self._lower[0])
        return (-self._lower[0] + self._upper[0]) / 2

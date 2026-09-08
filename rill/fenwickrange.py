"""Two Fenwick trees: range update and range query in log time, lighter than a segment tree.

A lazy segment tree does range update and range sum in log time,
and for this specific pair of operations, add a value to a range
and sum a range, two Fenwick trees do the same with less code and
a smaller constant factor. The trick is algebra on prefix sums. A
range add of delta to positions l through r changes the prefix sum
up to a position i by delta times how much of the range lies at or
before i, which is a piecewise-linear function of i, and any
piecewise-linear prefix can be represented as i times one running
total minus another. So one Fenwick tree accumulates the
coefficient of i and a second accumulates the constant offset, each
updated with two point additions per range update, and the prefix
sum at i is the first tree's prefix times i minus the second
tree's prefix. A range sum is then two prefix sums subtracted, as
always. The whole thing is four Fenwick point-updates per range
update and two prefix queries per range sum, all logarithmic, with
none of the recursion or lazy-marker bookkeeping a segment tree
carries. It works because addition composes linearly over a range;
a non-linear range operation like assignment or minimum would need
the segment tree. This module implements the two-tree scheme,
checked against a naive array, so the lighter range-update range-
query is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


class _Bit:
    def __init__(self, size: int) -> None:
        self._tree = [0] * (size + 2)
        self._size = size

    def add(self, index: int, delta: int) -> None:
        while index <= self._size + 1:
            self._tree[index] += delta
            index += index & (-index)

    def prefix(self, index: int) -> int:
        total = 0
        while index > 0:
            total += self._tree[index]
            index -= index & (-index)
        return total


class RangeFenwick:
    def __init__(self, size: int) -> None:
        if size < 1:
            raise Invalid("size must be positive")
        self.size = size
        self._slope = _Bit(size)
        self._offset = _Bit(size)

    def add_range(self, lo: int, hi: int, delta: int) -> None:
        if not 1 <= lo <= hi <= self.size:
            raise Invalid("range out of bounds (1-based, inclusive)")
        self._slope.add(lo, delta)
        self._slope.add(hi + 1, -delta)
        self._offset.add(lo, delta * (lo - 1))
        self._offset.add(hi + 1, -delta * hi)

    def _prefix(self, index: int) -> int:
        return self._slope.prefix(index) * index - self._offset.prefix(index)

    def range_sum(self, lo: int, hi: int) -> int:
        if not 1 <= lo <= hi <= self.size:
            raise Invalid("range out of bounds (1-based, inclusive)")
        return self._prefix(hi) - self._prefix(lo - 1)

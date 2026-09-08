"""Sparse table: O(1) range minimum on static data, because min tolerates overlap.

A range-minimum query over data that never changes can be answered
in constant time, faster than the logarithmic segment tree, by
precomputing the minimum of every power-of-two-length block. Any
range is then covered by two such blocks that may overlap: the
block of the largest power of two that fits, anchored at the left
end, and another of the same length anchored at the right end,
and the answer is the smaller of their two precomputed minima. The
overlap between the two blocks does not matter, and that is the
whole trick, because minimum is idempotent, taking the min of a
value twice is the same as once, so covering some elements in both
blocks changes nothing. That is why this works for min, max, and
gcd but not for sum, where double-counting the overlap would be
wrong and a range must be tiled by disjoint blocks instead. The
build is O(n log n) and every query afterward is two lookups and a
comparison, but nothing can be updated without rebuilding, so the
sparse table is the segment tree's static counterpart: give up
updates, gain a constant-time query. This module builds the table
and answers range minima, checked against a brute-force scan, so
the constant-time query on immutable data is measured.
"""

from __future__ import annotations

from rill.errors import Invalid


class SparseTable:
    def __init__(self, values: list[int]) -> None:
        if not values:
            raise Invalid("cannot build a sparse table over nothing")
        self._n = len(values)
        self._log = [0] * (self._n + 1)
        for i in range(2, self._n + 1):
            self._log[i] = self._log[i // 2] + 1
        self._table = [list(values)]
        level = 1
        while (1 << level) <= self._n:
            span = 1 << level
            previous = self._table[level - 1]
            row = [
                min(previous[i], previous[i + (span >> 1)])
                for i in range(self._n - span + 1)
            ]
            self._table.append(row)
            level += 1

    def range_min(self, lo: int, hi: int) -> int:
        if not 0 <= lo < hi <= self._n:
            raise Invalid(f"range [{lo}, {hi}) out of bounds")
        length = hi - lo
        k = self._log[length]
        return min(self._table[k][lo], self._table[k][hi - (1 << k)])

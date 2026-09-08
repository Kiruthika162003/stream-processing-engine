"""Prefix sums: range totals in constant time, paid for with a static array.

A range-sum query, the total between two positions, is answered
in constant time by precomputing prefix sums: an array whose i-th
entry is the sum of everything before position i, so the sum of
any half-open range is one prefix minus another, a single
subtraction no matter how wide the range. The build is one linear
pass and every query afterward is O(1), which is unbeatable when
the data does not change. The catch is exactly that it must not
change: updating one element shifts every prefix after it, so a
point update costs a linear rebuild, which is why prefix sums are
the right structure for a static or append-mostly dataset and the
wrong one for a mutating one. That is the trade against a Fenwick
tree, which accepts a logarithmic query to buy a logarithmic
update, so the choice between them is a question of whether the
data is read-only or live: read-only wants the constant-time
prefix array, live wants the tree. This module builds the prefix
array and answers range sums by subtraction, so the constant-time
query is a measured operation and the immutability is the
explicit price stated rather than discovered on the first update.
"""

from __future__ import annotations

from rill.errors import Invalid


class PrefixSum:
    def __init__(self, values: list[int]) -> None:
        self._prefix = [0]
        for value in values:
            self._prefix.append(self._prefix[-1] + value)

    def range_sum(self, lo: int, hi: int) -> int:
        size = len(self._prefix) - 1
        if not 0 <= lo <= hi <= size:
            raise Invalid(f"range [{lo}, {hi}) out of bounds for {size} elements")
        return self._prefix[hi] - self._prefix[lo]

    def total(self) -> int:
        return self._prefix[-1]

    def size(self) -> int:
        return len(self._prefix) - 1

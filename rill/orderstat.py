"""Order statistics: rank and select over a stream, both logarithmic, on a Fenwick of counts.

Two questions come up over and over on a stream of numbers: how
many values so far are at most x, its rank, and what is the kth
smallest value, its select. A sorted list answers both by binary
search but pays a linear insert to keep itself sorted, and a hash
of counts answers neither without a scan. A Fenwick tree over the
value domain answers both in logarithmic time and inserts in
logarithmic time too. Each value inserted increments the Fenwick
bucket for that value, so the prefix sum up to x is exactly the
count of values at most x, the rank, read in a single Fenwick
prefix query. Select is the inverse: walk down the Fenwick tree
choosing, at each level, whether the kth smallest lies in the
already-counted left span or beyond it, which finds the smallest
value whose prefix count reaches k, again logarithmic. So a
running median, a percentile, a rank threshold, all reduce to
these two operations over the same structure, with insert, rank,
and select all logarithmic in the value range rather than linear
in the count of values. This module keeps the Fenwick of counts
and answers rank and select, so the log-time order statistics are
measured operations, checked against a sorted reference.
"""

from __future__ import annotations

from rill.errors import Invalid


class OrderStatistics:
    def __init__(self, max_value: int) -> None:
        if max_value < 1:
            raise Invalid("max_value must be positive")
        self.max_value = max_value
        self._tree = [0] * (max_value + 1)
        self._count = 0

    def insert(self, value: int) -> None:
        if not 1 <= value <= self.max_value:
            raise Invalid(f"value {value} outside [1, {self.max_value}]")
        self._count += 1
        index = value
        while index <= self.max_value:
            self._tree[index] += 1
            index += index & (-index)

    def rank(self, value: int) -> int:
        if value < 0:
            raise Invalid("value cannot be negative")
        index = min(value, self.max_value)
        total = 0
        while index > 0:
            total += self._tree[index]
            index -= index & (-index)
        return total

    def select(self, k: int) -> int:
        if not 1 <= k <= self._count:
            raise Invalid(f"k must be in [1, {self._count}]")
        position = 0
        remaining = k
        log = self.max_value.bit_length()
        for level in range(log, -1, -1):
            step = position + (1 << level)
            if step <= self.max_value and self._tree[step] < remaining:
                position = step
                remaining -= self._tree[step]
        return position + 1

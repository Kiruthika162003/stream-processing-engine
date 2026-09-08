"""Sqrt decomposition: range sums in root-n, the simple middle between static and logarithmic.

Between the static prefix-sum array, which answers a range in
constant time but cannot be updated, and the Fenwick tree, which
does both in logarithmic time with bit tricks, sits a structure
that is neither the fastest nor the cleverest but the easiest to
reason about: square-root decomposition. It splits the array into
blocks of about root-n elements and keeps a running sum for each
block. A point update changes one element and its block's sum, a
constant amount of work. A range sum walks the partial block at
each end element by element and adds the precomputed sum of every
whole block in between, so it touches at most about two root-n
partial elements and root-n block sums, giving a root-n query. The
appeal is not the asymptotics, which the Fenwick tree beats, but
that the idea is transparent and generalizes to operations a
Fenwick cannot express as easily, range minimum, range assignment,
by storing more per block. It is the structure to reach for when
the operation is unusual and the log-time cleverness would be
fiddly to adapt, trading a root-n query for a scheme anyone can
verify at a glance. This module keeps the blocks and their sums,
updates a point, and answers a range, checked against a naive
array, so the root-n query is correct and its simplicity is on
display.
"""

from __future__ import annotations

import math

from rill.errors import Invalid


class SqrtDecomposition:
    def __init__(self, values: list[int]) -> None:
        if not values:
            raise Invalid("cannot decompose an empty array")
        self._values = list(values)
        self._block = max(1, math.isqrt(len(values)))
        count = (len(values) + self._block - 1) // self._block
        self._sums = [0] * count
        for index, value in enumerate(values):
            self._sums[index // self._block] += value

    def update(self, index: int, value: int) -> None:
        if not 0 <= index < len(self._values):
            raise Invalid("index out of range")
        block = index // self._block
        self._sums[block] += value - self._values[index]
        self._values[index] = value

    def range_sum(self, lo: int, hi: int) -> int:
        if not 0 <= lo <= hi < len(self._values):
            raise Invalid("range out of bounds (inclusive)")
        total = 0
        index = lo
        while index <= hi:
            if index % self._block == 0 and index + self._block - 1 <= hi:
                total += self._sums[index // self._block]
                index += self._block
            else:
                total += self._values[index]
                index += 1
        return total

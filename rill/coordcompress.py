"""Coordinate compression: replace sparse values with dense ranks, order intact.

Many array structures, a Fenwick tree or a bucket count, are indexed
by value and cost memory proportional to the range of the values,
not the count of them. When a few thousand events carry timestamps
or ids spread across a huge range, that range is mostly empty and
allocating for it is waste. Coordinate compression removes the waste
by replacing each distinct value with its rank, its position in the
sorted order of the distinct values, so a handful of values scattered
across billions collapse to the dense integers zero through the
distinct count minus one. The mapping is built by sorting the
distinct values once and assigning each its index; looking a value
up afterward is a binary search into that sorted list. The property
that makes it safe for order-sensitive work is that it is strictly
monotonic: value a is less than value b exactly when the rank of a
is less than the rank of b, so anything that depends only on the
relative order of values, sorting, comparisons, prefix counts,
median finding, gives the identical answer on the compressed
coordinates. What it does not preserve is distance: the gap between
consecutive ranks is always one regardless of the true gap, so
compression is wrong for anything summing actual value magnitudes.
The finding worth stating is that the transform trades away
magnitude to buy density, keeping order exactly, so it is right for
rank and count queries and wrong for value sums. This module builds
the compressor and maps values to ranks and back, and a test checks
the mapping is order-preserving and round-trips, so the monotonicity
is confirmed.
"""

from __future__ import annotations

from bisect import bisect_left

from rill.errors import Invalid


class Compressor:
    def __init__(self, values: list[int]) -> None:
        if values is None:
            raise Invalid("values must not be None")
        self._sorted = sorted(set(values))

    def __len__(self) -> int:
        return len(self._sorted)

    def rank(self, value: int) -> int:
        idx = bisect_left(self._sorted, value)
        if idx == len(self._sorted) or self._sorted[idx] != value:
            raise Invalid("value was not among the compressed coordinates")
        return idx

    def value(self, rank: int) -> int:
        if rank < 0 or rank >= len(self._sorted):
            raise Invalid("rank is out of range")
        return self._sorted[rank]

    def compress(self, values: list[int]) -> list[int]:
        return [self.rank(v) for v in values]

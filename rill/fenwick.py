"""Fenwick tree: running prefix sums where both the update and the query are log n.

A stream that maintains a histogram and keeps asking how many
values fall at or below some threshold, for a rank or a running
quantile, faces a bad trade with a plain array: keep prefix sums
and every point update rewrites the whole tail in O(n), or keep
raw counts and every query re-adds a prefix in O(n). The Fenwick
tree, a binary indexed tree, makes both sides logarithmic by
storing partial sums over ranges whose lengths are powers of two,
so a point update touches only the O(log n) cells whose ranges
cover that index and a prefix query sums only the O(log n) cells
that tile the prefix. The trick is the lowest-set-bit step: adding
that bit walks an index up through the cells that include it, and
subtracting it walks down through the cells that partition a
prefix, and both walks are as long as the index has bits. This
module keeps the tree, updates a point, answers a prefix and a
range sum, and counts the cells each walk touches, so the log-not-
linear cost is a number the test checks against the naive tail
rewrite it replaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Fenwick:
    size: int
    _tree: list[int] = field(default_factory=list)
    _touches: int = 0

    def __post_init__(self) -> None:
        if self.size < 1:
            raise Invalid("size must be positive")
        self._tree = [0] * (self.size + 1)

    def add(self, index: int, delta: int) -> None:
        if not 0 <= index < self.size:
            raise Invalid(f"index {index} out of range")
        self._touches = 0
        cursor = index + 1
        while cursor <= self.size:
            self._tree[cursor] += delta
            self._touches += 1
            cursor += cursor & (-cursor)

    def prefix(self, index: int) -> int:
        if not 0 <= index < self.size:
            raise Invalid(f"index {index} out of range")
        self._touches = 0
        cursor = index + 1
        total = 0
        while cursor > 0:
            total += self._tree[cursor]
            self._touches += 1
            cursor -= cursor & (-cursor)
        return total

    def range_sum(self, lo: int, hi: int) -> int:
        if lo > hi:
            raise Invalid("lo must not exceed hi")
        below = self.prefix(lo - 1) if lo > 0 else 0
        return self.prefix(hi) - below

    def last_touches(self) -> int:
        return self._touches

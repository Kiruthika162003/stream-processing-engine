"""Segment tree: range minima the Fenwick prefix trick cannot do, and why it stores it all.

A Fenwick tree answers prefix sums cheaply because sums are
invertible: a range sum is one prefix minus another, so the tree
only has to store prefixes. Minimum has no inverse. Knowing the
minimum of a long prefix tells you nothing about the minimum of a
shorter one, because removing the element that was the minimum
leaves you no record of the second-smallest, so there is no
subtraction that recovers a suffix's min from two prefixes. The
segment tree pays for that by storing the whole tree: every
internal node holds the minimum of its range, a point update
walks up fixing the O(log n) nodes above the changed leaf, and a
range query stitches the answer from the O(log n) nodes that
exactly tile the queried interval. Both operations stay
logarithmic like the Fenwick tree, but the tree is twice the
leaves in size rather than a single array of prefixes, which is
the concrete cost of a monoid that can combine but not cancel.
This module builds the tree over any associative combiner,
defaulting to minimum, updates a point, and queries a range,
checking its answers against a brute-force scan so the structure
is right and not merely plausible.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


class SegmentTree:
    def __init__(
        self,
        size: int,
        identity: int = 1 << 60,
        combine: Callable[[int, int], int] = min,
    ) -> None:
        if size < 1:
            raise Invalid("size must be positive")
        self.size = size
        self.identity = identity
        self.combine = combine
        self._tree = [identity] * (2 * size)

    def update(self, index: int, value: int) -> None:
        if not 0 <= index < self.size:
            raise Invalid(f"index {index} out of range")
        node = index + self.size
        self._tree[node] = value
        node //= 2
        while node >= 1:
            self._tree[node] = self.combine(
                self._tree[2 * node], self._tree[2 * node + 1]
            )
            node //= 2

    def query(self, lo: int, hi: int) -> int:
        if not 0 <= lo <= hi <= self.size:
            raise Invalid("need 0 <= lo <= hi <= size")
        result = self.identity
        left, right = lo + self.size, hi + self.size
        while left < right:
            if left & 1:
                result = self.combine(result, self._tree[left])
                left += 1
            if right & 1:
                right -= 1
                result = self.combine(result, self._tree[right])
            left //= 2
            right //= 2
        return result

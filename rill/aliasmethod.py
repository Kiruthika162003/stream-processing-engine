"""Alias method: draw from a weighted distribution in constant time per draw.

The obvious way to sample an item in proportion to a weight is to
build the running total of the weights, draw a uniform number in
that total, and binary search for the bucket it lands in, which is
log n per draw. The alias method does better: after a linear-time
setup it draws in constant time, no search at all. The setup packs
the distribution into n columns each of equal width, where a column
holds at most two items, a primary and an alias, split by a
threshold. A draw picks a column uniformly, which is one integer
draw, then flips a biased coin against the column's threshold to
choose between the column's two items, which is one float compare.
The construction is the clever part. Scale every probability by n,
so the average is one. An item whose scaled probability is below
one is "small", it cannot fill a column alone, and one at or above
one is "large". Repeatedly pair a small item with a large one: the
small item takes its column up to its threshold, the large item
donates the rest of that column and is reduced by what it gave, and
then the large item is re-sorted as small or large by whether it
still exceeds one. Each pairing finalizes one column, so the whole
build is linear. The distinguishing property, worth stating because
it is what makes the method pay, is that the per-draw cost does not
grow with the number of items, unlike the prefix-sum search whose
cost is the log of the item count. This module builds the tables
and draws, and a test checks the empirical frequency over many
draws tracks the target weights, so the constant-time sampler is
shown to be correct as well as fast.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


class AliasSampler:
    def __init__(self, weights: list[float]) -> None:
        if weights is None:
            raise Invalid("weights must not be None")
        if not weights:
            raise Invalid("weights must not be empty")
        if any(w < 0 for w in weights):
            raise Invalid("weights must not be negative")
        total = sum(weights)
        if total <= 0:
            raise Invalid("weights must sum to a positive number")
        n = len(weights)
        scaled = [w * n / total for w in weights]
        self._prob: list[float] = [0.0] * n
        self._alias: list[int] = [0] * n
        small = [i for i, p in enumerate(scaled) if p < 1.0]
        large = [i for i, p in enumerate(scaled) if p >= 1.0]
        while small and large:
            s = small.pop()
            g = large.pop()
            self._prob[s] = scaled[s]
            self._alias[s] = g
            scaled[g] = scaled[g] - (1.0 - scaled[s])
            if scaled[g] < 1.0:
                small.append(g)
            else:
                large.append(g)
        for leftover in large + small:
            self._prob[leftover] = 1.0

    def __len__(self) -> int:
        return len(self._prob)

    def draw(self, column: Callable[[int], int], coin: Callable[[], float]) -> int:
        col = column(len(self._prob))
        if col < 0 or col >= len(self._prob):
            raise Invalid("column picker returned an out-of-range index")
        return col if coin() < self._prob[col] else self._alias[col]

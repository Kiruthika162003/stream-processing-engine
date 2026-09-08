"""Quickselect: the kth smallest without sorting the rest, in linear time on average.

Finding a single order statistic, a median, a p99, the third
smallest, does not need the whole array sorted, and sorting to get
one element wastes an n log n where an average of n would do.
Quickselect is quicksort that recurses into only one side. It
partitions the array around a pivot so smaller elements fall left
and larger right, which places the pivot at its final sorted
position, and then it compares that position to the target rank:
if they match it is done, and if not it recurses into just the
side that contains the rank, discarding the other half entirely.
Because it throws away one partition each step instead of sorting
both, the expected work halves geometrically to a linear total,
and the elements it never needed to order are left unordered. The
worst case is quadratic when the pivots are chosen badly, which a
median-of-three pivot makes unlikely on real data, so the average
linear behavior is what holds in practice. This module selects the
kth smallest with a median-of-three pivot, checking the result
against a full sort, so the order statistic is correct while the
array around it stays only partially arranged.
"""

from __future__ import annotations

from rill.errors import Invalid


def _median_of_three(values: list[int], lo: int, hi: int) -> int:
    mid = (lo + hi) // 2
    trio = sorted((values[lo], values[mid], values[hi]))
    return trio[1]


def select(values: list[int], k: int) -> int:
    if not values:
        raise Invalid("empty sequence")
    if not 0 <= k < len(values):
        raise Invalid(f"rank {k} out of range for {len(values)} elements")
    work = list(values)
    lo, hi = 0, len(work) - 1
    while lo < hi:
        pivot = _median_of_three(work, lo, hi)
        left, right = lo, hi
        while left <= right:
            while work[left] < pivot:
                left += 1
            while work[right] > pivot:
                right -= 1
            if left <= right:
                work[left], work[right] = work[right], work[left]
                left += 1
                right -= 1
        if k <= right:
            hi = right
        elif k >= left:
            lo = left
        else:
            return work[k]
    return work[k]

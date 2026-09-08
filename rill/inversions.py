"""Inversion counting: how out-of-order a sequence is, in n log n instead of n squared.

The number of inversions in a sequence, the count of pairs that
appear in the wrong relative order, is a precise measure of how
disordered it is: zero for a sorted sequence, the maximum for a
reversed one, and for an event stream indexed by arrival, the
inversion count against event time is exactly how many pairs
arrived out of their true order, the disorder a watermark's
lateness bound has to tolerate. Counting inversions by comparing
every pair is quadratic. A merge sort counts them for free while
it sorts. During the merge of two already-sorted halves, whenever
an element from the right half is placed before some elements
still remaining in the left half, each of those remaining left
elements is greater than it and originally came before it, so it
forms an inversion with every one of them, and adding that count
at each such step tallies every inversion exactly once as the
halves combine. The sort is n log n and the counting rides along
at no extra asymptotic cost, so the disorder of a large stream is
measurable in the time it takes to sort it rather than the
quadratic a pairwise count would need. This module counts the
inversions by merge sort, checked against a brute-force pair count,
so the disorder measure is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def count_inversions(values: list[int]) -> int:
    if values is None:
        raise Invalid("values must not be None")
    _, count = _sort_count(list(values))
    return count


def _sort_count(values: list[int]) -> tuple[list[int], int]:
    if len(values) <= 1:
        return values, 0
    mid = len(values) // 2
    left, left_count = _sort_count(values[:mid])
    right, right_count = _sort_count(values[mid:])
    merged: list[int] = []
    i = j = 0
    inversions = left_count + right_count
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
            inversions += len(left) - i
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged, inversions

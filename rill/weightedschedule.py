"""Weighted interval scheduling: greedy picks the most intervals, DP picks the most value.

Choosing non-overlapping intervals to maximize their count has an
optimal greedy, earliest finish time, but attach a weight to each
interval and ask for the maximum total weight instead, and that
greedy falls apart. A single interval worth a fortune can overlap
and exclude several cheap ones, so a strategy that counts
intervals, or even one that always takes the earliest-finishing
compatible interval, will happily trade the fortune for a handful
of pennies. The maximum-weight version needs dynamic programming.
Sort the intervals by end time, and for each one decide between
two futures: skip it and keep the best weight achievable from the
intervals before it, or take it and add its weight to the best
weight achievable from the intervals that end at or before this
one starts, found by a binary search over the sorted ends. The
better of those two is this interval's answer, and the last one's
answer is the optimum over the whole set. The lesson is that
adding weights changes the problem's character: the count version
is greedy-optimal and the weight version is not, and using the
count greedy on weighted intervals silently leaves value on the
table. This module runs the DP and, for contrast, the count
greedy's weight, so the gap is measured on a case the greedy
loses.
"""

from __future__ import annotations

from bisect import bisect_right

from rill.errors import Invalid


def max_weight(intervals: list[tuple[int, int, int]]) -> int:
    for start, end, weight in intervals:
        if end < start or weight < 0:
            raise Invalid("interval end before start, or negative weight")
    if not intervals:
        return 0
    ordered = sorted(intervals, key=lambda iv: iv[1])
    ends = [end for _, end, _ in ordered]
    best = [0] * (len(ordered) + 1)
    for index, (start, _, weight) in enumerate(ordered, start=1):
        compatible = bisect_right(ends, start, 0, index - 1)
        take = weight + best[compatible]
        best[index] = max(best[index - 1], take)
    return best[-1]


def greedy_weight(intervals: list[tuple[int, int, int]]) -> int:
    ordered = sorted(intervals, key=lambda iv: iv[1])
    total = 0
    last_end = None
    for start, end, weight in ordered:
        if last_end is None or start >= last_end:
            total += weight
            last_end = end
    return total

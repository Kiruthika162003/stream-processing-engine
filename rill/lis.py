"""Longest increasing subsequence: the length of the best rising trend, in n log n.

The longest increasing subsequence of a series, the longest rising
trend that need not be contiguous, measures how much of a signal
moves in one direction through the noise, and the textbook dynamic
program finds it in quadratic time by comparing every pair.
Patience sorting finds the same length in n log n by dealing the
values into piles like the card game: each value is placed on the
leftmost pile whose top is at least as large, replacing that top,
and a value larger than every pile top starts a new pile on the
right. The number of piles at the end is the length of the longest
increasing subsequence, because each pile's tops are decreasing
and a value can only extend a subsequence by landing to the right
of a smaller one. Finding the pile for each value is a binary
search over the pile tops, which are kept sorted by construction,
so the whole thing is one pass with a log-time placement per
value. This module deals the piles and returns the count, checked
against the quadratic dynamic program so the n-log-n answer is
correct, and the point is that the pile tops are exactly the
structure that turns the pairwise comparison into a binary search.
"""

from __future__ import annotations

from bisect import bisect_left

from rill.errors import Invalid


def lis_length(values: list[int]) -> int:
    if not values:
        raise Invalid("empty series")
    tops: list[int] = []
    for value in values:
        position = bisect_left(tops, value)
        if position == len(tops):
            tops.append(value)
        else:
            tops[position] = value
    return len(tops)

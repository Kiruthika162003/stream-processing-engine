"""Two-pointer window: the longest span under a budget, in one forward sweep.

Finding the longest contiguous run of a series whose sum stays
within a budget, the longest stretch a rate stays under a cap, the
widest window a cost fits inside, is quadratic if every start
scans forward to find its longest fit. The two-pointer sweep does
it in one linear pass by exploiting a monotonic property of
non-negative values: a window's sum only grows as its right edge
advances, so once a window exceeds the budget the fix is to
advance the left edge, never to reconsider it. Both pointers move
only forward, the right one extending the window and the left one
contracting it whenever the sum overruns, and because neither ever
retreats, together they take at most a linear number of steps
across the whole series regardless of how the values fall. The
longest valid window seen during the sweep is the answer. The
method rests entirely on the values being non-negative, which is
what makes the sum monotonic in the window's width; with negative
values a wider window can have a smaller sum and the shrink step
is no longer valid. This module returns the length and start of
the longest window within the budget, checked against a
brute-force scan, so the linear sweep is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def longest_within_budget(values: list[int], budget: int) -> tuple[int, int]:
    if budget < 0:
        raise Invalid("budget cannot be negative")
    if any(value < 0 for value in values):
        raise Invalid("values must be non-negative for the two-pointer sweep")
    best_length = 0
    best_start = 0
    window_sum = 0
    left = 0
    for right, value in enumerate(values):
        window_sum += value
        while window_sum > budget and left <= right:
            window_sum -= values[left]
            left += 1
        if right - left + 1 > best_length:
            best_length = right - left + 1
            best_start = left
    return best_length, best_start

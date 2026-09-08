"""Kadane's algorithm: the best contiguous window in one pass, and the all-negative trap.

Finding the contiguous stretch of a series with the largest sum,
the most profitable window of a signed metric, the busiest span
of a load delta, looks like it needs to try every start and end,
which is quadratic. Kadane does it in one pass with a single
running idea: the best window ending at the current position is
either this element alone or this element appended to the best
window ending just before it, whichever is larger, and the answer
is the largest such running best over the whole series. Extending
the previous window is worth it exactly when that previous best
was positive, and starting fresh is worth it when it was negative,
so the running sum resets whenever it would drag the current
element down. The trap everyone hits first is the all-negative
series: a version that resets the running sum to zero on a
negative total will report an empty window of sum zero, which is
wrong when every element is negative and the true answer is the
single least-negative element. Handling it means seeding the best
with the first element rather than zero and never preferring the
empty window. This module returns the max sum and the window that
achieves it, checked against a brute-force scan so the one-pass
answer, all-negative case included, is correct and not just fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def max_subarray(values: list[int]) -> tuple[int, int, int]:
    if not values:
        raise Invalid("empty series has no subarray")
    best_sum = values[0]
    best_lo, best_hi = 0, 0
    current = values[0]
    start = 0
    for index in range(1, len(values)):
        value = values[index]
        if current < 0:
            current = value
            start = index
        else:
            current += value
        if current > best_sum:
            best_sum = current
            best_lo, best_hi = start, index
    return best_sum, best_lo, best_hi

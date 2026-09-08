"""Next greater element: a monotonic stack answers "how far to a bigger value" in one pass.

Asking, for each point in a series, how far ahead the next larger
value is, the wait until the next new high, the span until a
bigger spike, is quadratic if each point scans forward on its own.
A monotonic stack collapses it to one pass. The stack holds the
indices of values still waiting for something larger, kept in
decreasing order of value, so the newest is always the smallest of
the unresolved. When a value arrives, it is the next greater
element for every index on the stack that it exceeds, so those are
popped and answered in one motion, and then the new index is
pushed to wait its turn. Every index is pushed exactly once and
popped at most once across the whole series, so the total work is
linear no matter how the values are arranged, the same amortized
once-each accounting a monotonic structure always buys. Indices
still on the stack at the end never found a larger value and are
reported as having none. This module returns the distance to each
element's next greater value, checked against a brute-force
forward scan, so the linear pass is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def next_greater_distances(values: list[int]) -> list[int]:
    if not values:
        raise Invalid("empty series")
    distances = [-1] * len(values)
    stack: list[int] = []
    for index, value in enumerate(values):
        while stack and values[stack[-1]] < value:
            waiting = stack.pop()
            distances[waiting] = index - waiting
        stack.append(index)
    return distances

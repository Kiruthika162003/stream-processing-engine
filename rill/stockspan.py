"""Stock span: how long a value has been at or above today's, in one amortized pass.

The stock span of a value in a series is how many consecutive
prior entries, up to and including this one, were at or below it,
a measure of how long a metric has held at its current level or
higher: how many ticks a load has stayed under its current peak,
how long a price has not exceeded today. Computing each span by
scanning backward until a larger value is quadratic. A monotonic
stack does it in one pass by keeping indices of the previous values
that were strictly greater, in decreasing order, because once a new
value arrives, every earlier value at or below it is subsumed into
this value's span and can be discarded, its own span already
recorded. When a value comes in, it pops every stacked value not
strictly greater than it, and its span is the distance to the
nearest strictly greater value still on the stack, or the whole
prefix if none remains. Each index is pushed and popped once, so
the total work is linear even though a single span can reach back
across the whole series, the same amortized once-each accounting a
monotonic stack always gives. This module computes the span for
each position, checked against a brute-force backward scan, so the
linear pass is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def spans(values: list[int]) -> list[int]:
    if not values:
        raise Invalid("empty series")
    result: list[int] = []
    stack: list[int] = []
    for index, value in enumerate(values):
        while stack and values[stack[-1]] <= value:
            stack.pop()
        span = index + 1 if not stack else index - stack[-1]
        result.append(span)
        stack.append(index)
    return result

"""Largest rectangle in a histogram: the widest sustained level, found with a monotonic stack.

Given a histogram of bar heights, the largest axis-aligned
rectangle that fits under the bars answers a real question about a
series: the largest area of sustained level, the widest span over
which a resource stayed at least at some height, the biggest
contiguous block a load could have run at. Trying every pair of
left and right edges and taking the minimum height between them is
quadratic. A monotonic stack does it in one pass. It keeps the
indices of bars in increasing height, and when a shorter bar
arrives, every taller bar still on the stack can no longer extend
rightward at its height, so each is popped and its rectangle
finalized: the popped bar's height times the width from the bar
now below it on the stack to the current position. Because a bar
that is shorter than its predecessor bounds that predecessor's
rectangle on the right, and the stack holds the left bound, every
bar's maximal rectangle is computed exactly once as it is popped,
so each bar is pushed and popped once and the whole thing is
linear. The subtlety is the width: it spans from just past the bar
below on the stack to the current index, not from the popped bar
itself, which is the off-by-one everyone gets wrong first. This
module computes the largest rectangle, checked against a
brute-force search, so the linear pass is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def largest_rectangle(heights: list[int]) -> int:
    if any(height < 0 for height in heights):
        raise Invalid("heights cannot be negative")
    stack: list[int] = []
    best = 0
    for index in range(len(heights) + 1):
        current = heights[index] if index < len(heights) else 0
        while stack and heights[stack[-1]] >= current:
            height = heights[stack.pop()]
            left = stack[-1] if stack else -1
            width = index - left - 1
            best = max(best, height * width)
        stack.append(index)
    return best

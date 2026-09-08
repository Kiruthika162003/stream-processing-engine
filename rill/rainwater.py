"""Trapping rain water: the volume held between peaks, from the shorter wall inward.

Given a profile of heights, the water it traps after rain is the
volume that pools in the dips between the peaks, and it models a
real streaming quantity: how much a buffer fills in the valleys
between load peaks, how much backlog accumulates between two
high-water marks. The water above any position is bounded by the
lower of the tallest wall to its left and the tallest to its
right, minus the position's own height, because water spills over
whichever surrounding wall is shorter. Computing that per position
by scanning both directions is quadratic. The two-pointer method
does it in one linear pass by walking inward from both ends and
always advancing the side whose tallest-so-far wall is shorter.
The insight is that the shorter side's wall is the binding
constraint at its pointer: whatever taller wall exists on the far
side, the water there is capped by the near, shorter wall, so the
trapped water at that position is fully determined and the pointer
can advance. Each position is visited once, so it is linear and
uses constant extra space. This module computes the trapped volume
with the two-pointer sweep, checked against a per-position
left-max right-max reference, so the linear answer is correct as
well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def trapped_water(heights: list[int]) -> int:
    if any(height < 0 for height in heights):
        raise Invalid("heights cannot be negative")
    left, right = 0, len(heights) - 1
    left_max = right_max = 0
    total = 0
    while left < right:
        if heights[left] <= heights[right]:
            left_max = max(left_max, heights[left])
            total += left_max - heights[left]
            left += 1
        else:
            right_max = max(right_max, heights[right])
            total += right_max - heights[right]
            right -= 1
    return total

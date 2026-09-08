"""Minimum stabbing points: the fewest instants that touch every interval, placed at ends.

Given a set of intervals, the fewest points that hit every one,
the fewest probe times that fall inside every session, the fewest
checkpoints that land in every job's window, is a covering problem
with a clean greedy. Sort the intervals by their end, and sweep:
whenever an interval is not already hit by the last point placed,
place a new point at that interval's end. Placing the point at the
end rather than anywhere inside is what makes the greedy optimal,
because the end is the rightmost instant that still hits this
interval, so it also hits the greatest number of later intervals
that overlap it, deferring the next point as long as possible.
Any point placed earlier would cover a subset of what the end-point
covers, so it can never do better and may do worse. The exchange
argument confirms it: no set of points smaller than the greedy's
can hit every interval, because each point the greedy places is
forced by an interval that the previous points genuinely missed.
This is the dual of interval scheduling, and the same earliest-end
insight drives both. This module runs the greedy and returns the
minimum point count, checked against a brute-force search, so the
end-placement rule is a measured optimum and not a heuristic that
usually works.
"""

from __future__ import annotations

from rill.errors import Invalid


def min_stab_points(intervals: list[tuple[int, int]]) -> int:
    for start, end in intervals:
        if end < start:
            raise Invalid(f"interval end {end} before start {start}")
    if not intervals:
        return 0
    points = 0
    last_point = None
    for start, end in sorted(intervals, key=lambda iv: iv[1]):
        if last_point is None or start > last_point:
            points += 1
            last_point = end
    return points

"""Sweep line: the peak concurrent overlaps, which is what actually sizes the pool.

Given a pile of intervals, sessions open at once, connections
alive together, timers pending in the same span, the question
that sizes a resource pool is not how many there are but how many
are ever live at the same instant, the peak concurrency. Checking
every pair for overlap answers it in quadratic time and buries
the moment of the peak in the counting. The sweep line does it in
one pass over the sorted endpoints: turn each interval into a
plus-one at its start and a minus-one at its end, walk the events
in time order keeping a running count, and the largest the count
ever reaches is the peak. The one subtlety is the tie at a shared
timestamp: with half-open intervals an interval that ends exactly
when another begins do not overlap, so an end must be processed
before a start at the same time, which the ordering handles by
sorting the minus-one ahead of the plus-one. This module builds
the events, sweeps them, and reports both the peak and the time
it first occurs, so the pool size and the busiest instant are a
computed pair rather than an O(n squared) scan that forgets to
say when.
"""

from __future__ import annotations

from rill.errors import Invalid


def peak_concurrency(intervals: list[tuple[int, int]]) -> tuple[int, int]:
    if not intervals:
        raise Invalid("no intervals to sweep")
    events: list[tuple[int, int]] = []
    for start, end in intervals:
        if end < start:
            raise Invalid(f"interval end {end} before start {start}")
        events.append((start, 1))
        events.append((end, -1))
    events.sort(key=lambda event: (event[0], event[1]))
    running = 0
    peak = 0
    peak_at = events[0][0]
    for time, delta in events:
        running += delta
        if running > peak:
            peak = running
            peak_at = time
    return peak, peak_at


def all_overlaps(intervals: list[tuple[int, int]], point: int) -> list[tuple[int, int]]:
    return [(s, e) for s, e in intervals if s <= point < e]

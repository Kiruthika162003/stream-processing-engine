"""Interval set: keeping a minimal cover of ranges as new ones are added and merged in.

Tracking which ranges of a keyspace or a time axis have been
covered, which event-time windows a backfill has already
processed, which offsets a reprocess has filled, wants a set of
intervals that stays minimal: no two of its intervals overlap or
even touch, so it is always the smallest description of the ground
covered. Adding a new interval is where the work is. The new
interval may overlap several existing ones, or bridge a gap
between two that were separate, so the add must find every stored
interval that touches the new one, absorb them all into a single
merged interval spanning from the minimum start to the maximum
end, and drop the ones it absorbed. An interval that bridges two
previously separate intervals collapses all three into one, which
is the case a naive append-and-forget would miss, leaving the set
non-minimal and its coverage queries wrong. Because the intervals
are kept sorted and disjoint, the overlapping ones form a
contiguous run, found by locating where the new interval's ends
fall, so the merge touches only the affected run. This module adds
with merging, tests whether a point is covered, and reports the
total covered length, so the incremental minimal cover, and the
bridging merge a simple list would botch, are a checkable state.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class IntervalSet:
    _intervals: list[tuple[int, int]] = field(default_factory=list)

    def add(self, lo: int, hi: int) -> None:
        if hi < lo:
            raise Invalid("interval end before start")
        if hi == lo:
            return
        merged_lo, merged_hi = lo, hi
        kept: list[tuple[int, int]] = []
        for start, end in self._intervals:
            if end < merged_lo or start > merged_hi:
                kept.append((start, end))
            else:
                merged_lo = min(merged_lo, start)
                merged_hi = max(merged_hi, end)
        kept.append((merged_lo, merged_hi))
        kept.sort()
        self._intervals = kept

    def covers(self, point: int) -> bool:
        index = bisect_left(self._intervals, (point + 1,)) - 1
        if index < 0:
            return False
        start, end = self._intervals[index]
        return start <= point < end

    def total_length(self) -> int:
        return sum(end - start for start, end in self._intervals)

    def intervals(self) -> list[tuple[int, int]]:
        return list(self._intervals)

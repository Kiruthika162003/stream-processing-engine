"""Merging intervals: coalescing overlapping spans into the disjoint set they cover.

A pile of intervals, session windows that touch, busy spans that
overlap, reservations that abut, often needs collapsing into the
minimal set of disjoint spans covering the same ground, so
downstream sees one merged window instead of a tangle. The way
that works and the way that quietly does not both start by
sorting the intervals by start time, but the merge step is where a
naive version goes wrong. Walking the sorted intervals and
extending the current span whenever the next one starts within it
is correct only if the extension uses the maximum of the two ends,
not the latest interval's end, because a long interval can wholly
contain a later short one, and taking the short one's end would
shrink the merged span and expose ground the long interval still
covered. Getting that right, the merged span's end is the larger
of the current end and the incoming end, collapses the pile into
disjoint spans in one pass after the sort. Whether two touching
intervals merge is a boundary choice this module makes closed, so
a span ending where the next begins joins it. This module sorts,
merges with the max-end rule, and returns the disjoint cover, so
the coalescing is correct including the contained-interval case a
naive merge drops.
"""

from __future__ import annotations

from rill.errors import Invalid


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    for start, end in intervals:
        if end < start:
            raise Invalid(f"interval end {end} before start {start}")
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged

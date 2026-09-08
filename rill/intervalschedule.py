"""Interval scheduling: earliest-finish is optimal, and the tempting heuristics are not.

Choosing the most non-overlapping intervals from a set, the most
reservations that fit a room, the most tasks a worker can run
without conflict, has one greedy rule that is optimal and several
that look reasonable and are wrong. Sort by earliest finish time
and repeatedly take the next interval that starts after the last
one taken ends: this is provably optimal, because finishing
earliest leaves the most room for whatever follows, and an
exchange argument shows no other selection beats it. The
heuristics that fail are the intuitive ones. Earliest start time
fails because one interval that starts early and runs long blocks
everything behind it while contributing only one to the count.
Shortest duration fails because a short interval wedged across the
seam of two longer ones knocks out both to add one. The failures
are not rare edge cases, they are the normal shape of the
problem, which is why the earliest-finish rule is worth stating
precisely rather than reaching for whichever sort feels fair.
This module runs the optimal selection and the earliest-start
heuristic side by side, so the gap between them is a measured
count on a case where the tempting rule loses.
"""

from __future__ import annotations

from rill.errors import Invalid


def _validate(intervals: list[tuple[int, int]]) -> None:
    for start, end in intervals:
        if end < start:
            raise Invalid(f"interval end {end} before start {start}")


def max_nonoverlapping(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    _validate(intervals)
    chosen: list[tuple[int, int]] = []
    last_end = None
    for start, end in sorted(intervals, key=lambda iv: iv[1]):
        if last_end is None or start >= last_end:
            chosen.append((start, end))
            last_end = end
    return chosen


def by_earliest_start(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    _validate(intervals)
    chosen: list[tuple[int, int]] = []
    last_end = None
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        if last_end is None or start >= last_end:
            chosen.append((start, end))
            last_end = end
    return chosen

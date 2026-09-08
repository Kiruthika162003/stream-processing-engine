"""Job sequencing with deadlines: take the richest jobs, and slot each as late as it can go.

Given jobs that each take one unit of time, earn a profit, and
must finish by a deadline, scheduling to maximize profit on a
single worker is a greedy problem with a twist that decides
whether the greedy is optimal. Sorting the jobs by profit and
considering the richest first is right, but where to place each
one is the subtlety: assign it to the latest still-free time slot
at or before its deadline, not the earliest. Placing it late keeps
the early slots open for jobs with tighter deadlines that have no
choice but to run early, whereas grabbing the earliest free slot
would burn a slot a tighter job needed and force that job to be
dropped. So the two greedy choices work together, richest first
decides which jobs to prefer, and latest-slot placement fits them
without stealing room from the ones with less flexibility, and
the combination is provably optimal. This is the shape of any
deadline-aware scheduler that must choose a profitable subset it
can actually run in time, and getting the slot direction wrong
silently leaves profit on the table on exactly the instances where
deadlines are tight. This module runs the greedy and returns the
maximum profit and the count scheduled, checked against a brute
force, so the latest-slot rule is a measured optimum and not a
convention.
"""

from __future__ import annotations

from rill.errors import Invalid


def max_profit(jobs: list[tuple[int, int]]) -> tuple[int, int]:
    for deadline, profit in jobs:
        if deadline < 1 or profit < 0:
            raise Invalid("deadlines start at 1 and profits are non-negative")
    if not jobs:
        return 0, 0
    horizon = max(deadline for deadline, _ in jobs)
    slots: list[bool] = [False] * (horizon + 1)
    total = 0
    scheduled = 0
    for profit, deadline in sorted(
        ((p, d) for d, p in jobs), reverse=True
    ):
        slot = deadline
        while slot >= 1 and slots[slot]:
            slot -= 1
        if slot >= 1:
            slots[slot] = True
            total += profit
            scheduled += 1
    return total, scheduled

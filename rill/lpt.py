"""Longest-processing-time scheduling: place the big jobs first or the tail wrecks the makespan.

Assigning jobs to identical machines to finish as early as
possible, minimizing the makespan, is NP-hard exactly, but a
greedy rule gets close, and which greedy rule matters enormously.
List scheduling places each job on the machine that is currently
least loaded, which is sound, but the order the jobs arrive in
decides the quality. Feed the jobs smallest first and a large job
arriving last lands on top of an already-balanced load and spikes
one machine's finish time, so the makespan can approach twice the
optimal. Longest-processing-time scheduling sorts the jobs
largest first before the same greedy placement, so the big jobs
are placed while there is still room to balance them and the small
jobs at the end fill the gaps between, which bounds the makespan
to within a third above optimal rather than double. The intuition
is that the last job placed is what stretches the makespan, so you
want the last job to be small, which sorting descending
guarantees. This module runs the greedy placement in both orders
and reports the makespan, so the difference between putting the
big jobs first and letting them arrive last is a measured gap in
finish time rather than a worst-case bound on paper.
"""

from __future__ import annotations

from rill.errors import Invalid


def _schedule(jobs: list[int], machines: int) -> int:
    loads = [0] * machines
    for job in jobs:
        lightest = min(range(machines), key=lambda m: loads[m])
        loads[lightest] += job
    return max(loads)


def lpt_makespan(jobs: list[int], machines: int) -> int:
    if machines < 1:
        raise Invalid("need at least one machine")
    if any(job < 0 for job in jobs):
        raise Invalid("job sizes cannot be negative")
    return _schedule(sorted(jobs, reverse=True), machines)


def naive_makespan(jobs: list[int], machines: int) -> int:
    if machines < 1:
        raise Invalid("need at least one machine")
    if any(job < 0 for job in jobs):
        raise Invalid("job sizes cannot be negative")
    return _schedule(sorted(jobs), machines)

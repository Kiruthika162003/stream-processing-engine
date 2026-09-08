"""Schedulability: EDF fills the processor to the brim, rate-monotonic stops at 69 percent.

A set of periodic tasks, each a fraction of the processor equal
to its runtime over its period, is schedulable under different
policies up to different utilizations, and the gap between them
is real capacity left on the floor. Earliest-deadline-first, which
always runs the task whose deadline is nearest, is optimal for
this: a task set is EDF-schedulable exactly when its total
utilization is at most one, so EDF can fill the processor to 100
percent and miss nothing. Rate-monotonic, which assigns fixed
priorities by period so the fastest task always wins, is simpler
and more predictable but pays for it. Its guaranteed bound is n
times the quantity two to the one-over-n minus one, which starts
at one for a single task and falls as tasks are added, settling
toward the natural log of two, about 0.69, for many tasks. So a
task set whose utilization sits between that bound and one is
schedulable under EDF and fails the rate-monotonic guarantee: the
same hardware runs it or drops deadlines depending only on the
scheduling discipline. This module computes both tests and the
rate-monotonic bound, so the third of the processor that fixed
priority leaves unusable is a measured number.
"""

from __future__ import annotations

from rill.errors import Invalid


def _validate(utilizations: list[float]) -> None:
    if not utilizations:
        raise Invalid("no tasks to schedule")
    if any(util <= 0 for util in utilizations):
        raise Invalid("each utilization must be positive")


def rm_bound(count: int) -> float:
    if count < 1:
        raise Invalid("need at least one task")
    return count * (2 ** (1 / count) - 1)


def edf_schedulable(utilizations: list[float]) -> bool:
    _validate(utilizations)
    return sum(utilizations) <= 1.0 + 1e-9


def rm_schedulable(utilizations: list[float]) -> bool:
    _validate(utilizations)
    return sum(utilizations) <= rm_bound(len(utilizations)) + 1e-9

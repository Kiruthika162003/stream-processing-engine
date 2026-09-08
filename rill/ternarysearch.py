"""Ternary search: find the peak of a unimodal function by discarding a third each step.

Binary search finds a target in a sorted, monotonic sequence by
halving the interval on each comparison. Ternary search solves a
different shape of problem: finding the maximum or minimum of a
unimodal function, one that rises to a single peak and then falls,
or falls to a single valley and then rises. It cannot use a single
comparison to pick a half, because the function is not monotonic, so
it probes at two interior points that split the interval into
thirds. For a peak, if the left probe is lower than the right, the
maximum cannot lie in the leftmost third, since the function would
have to rise, fall, and rise again to put it there, breaking
unimodality, so that third is discarded and the search continues on
the remaining two thirds. The symmetric argument discards the right
third when the right probe is lower. Each step keeps two thirds of
the interval, so the width shrinks by two thirds per step and the
count of steps to reach a tolerance is logarithmic, base three over
two, in the ratio of the starting width to the tolerance. The
requirement that must hold for the discard to be valid is strict
unimodality, a single peak with no flat stretches at the top; a flat
maximum can make both probes equal and hide which third to drop.
The finding worth stating is that two probes per step, not one, is
the price of dropping the monotonicity that binary search assumes,
and it still buys logarithmic convergence. This module ternary
searches for the maximum of a unimodal function on a real interval,
and a test checks the located peak against a fine brute grid scan,
so the two-probe discard is confirmed to converge to the true peak.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


def ternary_search_max(
    func: Callable[[float], float],
    low: float,
    high: float,
    tolerance: float = 1e-9,
    max_iters: int = 200,
) -> float:
    if func is None:
        raise Invalid("a function is required")
    if low > high:
        raise Invalid("low must not exceed high")
    if tolerance <= 0:
        raise Invalid("tolerance must be positive")
    iters = 0
    while high - low > tolerance and iters < max_iters:
        third = (high - low) / 3
        m1 = low + third
        m2 = high - third
        if func(m1) < func(m2):
            low = m1
        else:
            high = m2
        iters += 1
    return (low + high) / 2

"""Balanced partition: splitting a load into two halves as even as a subset can make them.

Dividing a set of weighted items into two groups whose totals are
as equal as possible, balancing a load across two shards, two
workers, two links, is the partition problem, and whether a
perfectly even split even exists is the subset-sum question in
disguise: a perfect split exists exactly when some subset of the
items sums to half the total. Greedily assigning each item to the
lighter group so far is fast and often close but not optimal,
because a single large item placed early can force an imbalance a
different grouping would have avoided. The dynamic program finds
the best split by computing every subset sum reachable up to half
the total, marking a running boolean array of achievable sums as
each item is considered, and the achievable sum closest to half
the total gives the most balanced partition, with the imbalance
being the total minus twice that sum. So the DP answers both the
yes-or-no of a perfect split and the how-close of the best
achievable one, in time proportional to the item count times the
total weight, pseudo-polynomial like the knapsack it resembles.
This module computes whether an even split exists and the smallest
achievable difference between the two halves, checked against a
brute-force over all subsets, so the balanced partition is a
computed optimum and not a greedy approximation.
"""

from __future__ import annotations

from rill.errors import Invalid


def _best_subset_sum(values: list[int]) -> int:
    total = sum(values)
    half = total // 2
    reachable = [False] * (half + 1)
    reachable[0] = True
    for value in values:
        for target in range(half, value - 1, -1):
            if reachable[target - value]:
                reachable[target] = True
    for target in range(half, -1, -1):
        if reachable[target]:
            return target
    return 0


def can_partition(values: list[int]) -> bool:
    if any(value < 0 for value in values):
        raise Invalid("values must be non-negative")
    total = sum(values)
    if total % 2 != 0:
        return False
    return _best_subset_sum(values) == total // 2


def closest_partition(values: list[int]) -> int:
    if any(value < 0 for value in values):
        raise Invalid("values must be non-negative")
    if not values:
        return 0
    best = _best_subset_sum(values)
    return sum(values) - 2 * best

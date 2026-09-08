"""Fractional knapsack: the density greedy that is optimal here, exactly where 0/1 is not.

The zero-one knapsack punishes the value-density greedy, but make
the items divisible, so a fraction of an item can be taken for a
proportional fraction of its value, and that same greedy becomes
optimal. Sort the items by value per unit weight, take the densest
whole while it fits, and when the next item no longer fits whole,
take exactly the fraction of it that fills the remaining capacity.
This is optimal because divisibility removes the trap that sinks
the greedy on whole items: there is no situation where committing
to a dense item forecloses a better combination, since the budget
is always spent on the highest available density down to the last
unit, and any solution that used a lower-density unit while a
higher-density one was still available could be improved by
swapping them. So the two knapsacks sit on opposite sides of a
line drawn by a single modeling choice, divisibility: the
fractional one is greedy-solvable in n log n for the sort, and the
zero-one one is NP-hard and needs dynamic programming, from the
same items and the same objective. This module runs the greedy
fractional fill and returns the maximum value, so the density
rule's optimality on divisible items stands measured beside its
failure on indivisible ones.
"""

from __future__ import annotations

from rill.errors import Invalid


def max_value(items: list[tuple[int, int]], capacity: int) -> float:
    if capacity < 0:
        raise Invalid("capacity cannot be negative")
    if any(weight <= 0 or value < 0 for weight, value in items):
        raise Invalid("weights must be positive and values non-negative")
    remaining = capacity
    total = 0.0
    for weight, value in sorted(
        items, key=lambda item: item[1] / item[0], reverse=True
    ):
        if remaining <= 0:
            break
        take = min(weight, remaining)
        total += value * take / weight
        remaining -= take
    return total

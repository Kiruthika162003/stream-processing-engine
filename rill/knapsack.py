"""Zero-one knapsack: the density greedy is optimal for fractions, wrong for wholes.

Choosing items to maximize value within a weight budget has a
clean greedy when items are divisible: take them in order of value
per weight, filling with fractions, and the highest-density items
first is provably optimal. Make the items indivisible, take an
item whole or not at all, and that greedy breaks. It can grab a
high-density small item that then blocks a pair of slightly
lower-density items whose combined value is higher, because it
commits locally without seeing that the budget it spent could have
bought more elsewhere. The zero-one version needs dynamic
programming: build a table of the best value achievable for each
budget from zero up to the capacity, considering items one at a
time, where each item either is left out, keeping the best without
it, or is taken, adding its value to the best for the budget minus
its weight. The table's last cell is the optimum, computed in
capacity times item count. The lesson is that indivisibility
changes the problem's complexity class, turning a greedy-solvable
fractional problem into an NP-hard whole one that the DP handles
exactly at pseudo-polynomial cost. This module runs the DP and the
density greedy side by side, so the value the greedy leaves behind
on a whole-item budget is a measured gap.
"""

from __future__ import annotations

from rill.errors import Invalid


def knapsack(items: list[tuple[int, int]], capacity: int) -> int:
    if capacity < 0:
        raise Invalid("capacity cannot be negative")
    if any(weight < 0 or value < 0 for weight, value in items):
        raise Invalid("weights and values must be non-negative")
    best = [0] * (capacity + 1)
    for weight, value in items:
        for budget in range(capacity, weight - 1, -1):
            best[budget] = max(best[budget], best[budget - weight] + value)
    return best[capacity]


def greedy_density(items: list[tuple[int, int]], capacity: int) -> int:
    ordered = sorted(items, key=lambda item: item[1] / item[0], reverse=True)
    total = 0
    remaining = capacity
    for weight, value in ordered:
        if weight <= remaining:
            total += value
            remaining -= weight
    return total

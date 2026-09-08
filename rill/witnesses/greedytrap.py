"""Three items, a budget of fifty, and the density greedy that leaves sixty on the table.

The drill runs the classic knapsack trap: items weighing ten,
twenty, and thirty worth sixty, one hundred, and one hundred
twenty, against a budget of fifty, solved by the value-density
greedy and by the exact dynamic program. The greedy looks
unbeatable going in, since taking the highest value per weight
first is provably optimal when items can be split. The
measurement shows it losing badly on whole items: the greedy
grabs the densest ten-item and then the twenty-item for one
hundred sixty, which blocks the thirty-item, while the DP takes
the twenty and the thirty for two hundred twenty, sixty more from
the identical budget. The deposition keeps the unbeatable-looking
guess beside the measured gap, because the lesson is that
indivisibility, not the numbers, is what breaks the greedy: the
same value-density rule that is optimal for fractions commits to a
local choice that a whole-item budget cannot undo, and only the DP
sees the combination the greedy's first pick foreclosed.
"""

from __future__ import annotations

from rill.knapsack import greedy_density, knapsack
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    items = [(10, 60), (20, 100), (30, 120)]
    capacity = 50
    optimal = knapsack(items, capacity)
    greedy = greedy_density(items, capacity)
    numbers = {
        "capacity": capacity,
        "dp_optimal": optimal,
        "density_greedy": greedy,
        "value_left_behind": optimal - greedy,
    }
    holds = optimal == 220 and greedy == 160
    return Deposition(
        witness="greedytrap",
        claim=(
            "on items 10/20/30 worth 60/100/120 with a budget of 50, "
            "the value-density greedy took 160 and blocked the third "
            "item while the DP took 220, sixty more from the same "
            "budget, because indivisibility breaks the greedy"
        ),
        numbers=numbers,
        holds=holds,
    )

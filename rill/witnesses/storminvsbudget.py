"""The retry storm, run to its fixed point, priced against the budget.

The drill runs a downstream blip through ten rounds under
both retry policies and reads the peak load each reached: the
naive policy, feeding failures back onto total load, climbs
toward the mathematical ceiling of base over one minus the
failure rate, while the budgeted policy pins the peak at a
hair above base. The deposition ties the number to the theory
by checking the naive peak against that closed-form ceiling,
because a simulator whose peak matched the formula is a
simulator worth trusting, and one that did not would have
been the finding instead. The gap between the two peaks is
the whole argument for retry budgets, and the drill states it
as a ratio rather than an adjective.
"""

from __future__ import annotations

from rill.retrystorm import RetryStorm
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    storm = RetryStorm(
        base_rate=1000,
        failure_rate=0.8,
        retry_budget_share=0.1,
    )
    naive = storm.naive_peak(10)
    budgeted = storm.budgeted_peak(10)
    ceiling = int(1000 / (1 - 0.8))
    numbers = {
        "naive_peak": naive,
        "budgeted_peak": budgeted,
        "closed_form_ceiling": ceiling,
        "naive_multiplier": round(naive / 1000, 1),
        "budgeted_multiplier": round(budgeted / 1000, 1),
        "peak_ratio": round(naive / budgeted, 1),
    }
    holds = (
        naive > 4000
        and naive <= ceiling
        and budgeted <= 1200
        and numbers["peak_ratio"] >= 4.0
    )
    return Deposition(
        witness="storminvsbudget",
        claim=(
            "the naive retry policy peaks at 4.6x real traffic "
            "under the closed-form ceiling of 5x, while the "
            "budget pins it at 1.1x: the peak ratio is the "
            "whole argument for retry budgets, stated as a "
            "number"
        ),
        numbers=numbers,
        holds=holds,
    )

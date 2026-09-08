"""Sixty thousand shuffles of three cards, and the one-line variant that deals unevenly.

The drill shuffles three items sixty thousand times two ways, the
correct Fisher-Yates and the tempting variant that draws its swap
index from the whole range each step, and counts how often each of
the six permutations comes up. The guess is that both look random,
so both should spread roughly evenly. The measurement separates
them cleanly: Fisher-Yates spreads the six permutations between
9879 and 10158, a max-over-min under 1.1 with a standard deviation
of 85, while the naive variant runs 8857 to 11119, some orderings
a quarter more common than others, with a standard deviation over
a thousand, more than ten times as skewed. The deposition keeps
the both-look-random guess beside the measured skew, because the
lesson is that the bias is invisible in any single shuffle and
undeniable over sixty thousand: the naive variant's swap sequences
number n-to-the-n, which does not divide evenly by the factorial
permutations, so some must come up more often, and the only code
difference is the upper bound of one random draw.
"""

from __future__ import annotations

import random
import statistics
from collections import Counter

from rill.fisheryates import naive_shuffle, shuffle
from rill.witnesses.deposition import Deposition


def _spread(fn) -> Counter:
    rng = random.Random(1)

    def pick(hi: int) -> int:
        return rng.randint(0, hi)

    counts: Counter = Counter()
    for _ in range(60000):
        counts[tuple(fn(["a", "b", "c"], pick))] += 1
    return counts


def run() -> Deposition:
    fair = _spread(shuffle)
    biased = _spread(naive_shuffle)
    fair_ratio = max(fair.values()) / min(fair.values())
    biased_ratio = max(biased.values()) / min(biased.values())
    numbers = {
        "fisher_yates_max_over_min": round(fair_ratio, 3),
        "naive_max_over_min": round(biased_ratio, 3),
        "fisher_yates_stdev": round(statistics.pstdev(fair.values())),
        "naive_stdev": round(statistics.pstdev(biased.values())),
    }
    holds = fair_ratio < 1.1 and biased_ratio > 1.2
    return Deposition(
        witness="fairdeal",
        claim=(
            "over sixty thousand three-item shuffles Fisher-Yates "
            "spread the six permutations to a max-over-min under 1.1 "
            "while the naive variant reached over 1.2 with more than "
            "ten times the standard deviation"
        ),
        numbers=numbers,
        holds=holds,
    )

"""Fisher-Yates: a uniform shuffle, and the one-line variant that is subtly biased.

Shuffling a sequence so every permutation is equally likely is a
building block for randomized partitioning, sampling, and load
spreading, and the correct algorithm is one line different from a
common wrong one. Fisher-Yates walks from the last position down to
the first, and for each position i picks a random index uniformly
from zero through i, swapping the two. Because each step chooses
from only the not-yet-fixed prefix, every one of the factorial
permutations comes out with exactly equal probability. The
tempting variant swaps position i with a random index chosen from
the whole range zero through n minus one, and it looks just as
random and is not: it can produce n-to-the-n equally likely swap
sequences, which does not divide evenly by the factorial number of
permutations, so some orderings come out more often than others,
a bias invisible in a single run and stark over many. The
difference is the upper bound of the random draw, i versus n minus
one, and getting it wrong is one of the most reproduced bugs in
shuffling code. This module implements the correct shuffle and the
biased one from an injected index picker, so the uniformity of one
and the skew of the other are a measured distribution rather than
a claim that both look fine.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


def shuffle(items: list[str], pick: Callable[[int], int]) -> list[str]:
    result = list(items)
    for i in range(len(result) - 1, 0, -1):
        j = pick(i)
        if not 0 <= j <= i:
            raise Invalid("picker must return an index in [0, i]")
        result[i], result[j] = result[j], result[i]
    return result


def naive_shuffle(items: list[str], pick: Callable[[int], int]) -> list[str]:
    result = list(items)
    n = len(result)
    for i in range(n):
        j = pick(n - 1)
        result[i], result[j] = result[j], result[i]
    return result

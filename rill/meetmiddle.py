"""Meet in the middle: subset-sum in two-to-the-half-n by splitting the search.

Deciding whether some subset of n numbers sums to a target is the
classic subset-sum problem, and checking all two-to-the-n subsets is
exponential and quickly hopeless past forty or so items. Meet in the
middle halves the exponent, to two-to-the-n-over-two, which squares
the reach for the same work, forty items becoming eighty. The idea is
to split the numbers into two halves and enumerate the subset sums of
each half separately, each list holding two-to-the-half-n sums rather
than the full two-to-the-n. A target is reachable exactly when some
sum from the first list plus some sum from the second equals it. Found
naively that pairing is again quadratic in the list sizes, back to
two-to-the-n, so the second half is the trick: sort one list of sums,
then for each sum in the other binary search the sorted list for the
exact complement, target minus that sum. Sorting and searching cost
the half-size times its log, so the whole thing is dominated by the
two-to-the-half-n enumeration. The technique is not specific to
sums: it applies whenever a search space factors into two independent
halves whose partial results can be combined by a fast lookup, which
is why it recurs across knapsack variants and meet-in-the-middle
attacks in cryptography. The finding worth stating is that halving
the exponent comes entirely from replacing the cross-product pairing
with a sort-and-search over one half's results. This module decides
subset-sum by meet in the middle, and a test checks its yes-or-no
answer against the brute two-to-the-n enumeration, so the split is
confirmed to preserve the answer.
"""

from __future__ import annotations

from bisect import bisect_left

from rill.errors import Invalid


def _subset_sums(items: list[int]) -> list[int]:
    sums = [0]
    for x in items:
        sums += [s + x for s in sums]
    return sums


def subset_sum_reachable(items: list[int], target: int) -> bool:
    if items is None:
        raise Invalid("items must not be None")
    mid = len(items) // 2
    left = sorted(_subset_sums(items[:mid]))
    right = _subset_sums(items[mid:])
    for s in right:
        need = target - s
        idx = bisect_left(left, need)
        if idx < len(left) and left[idx] == need:
            return True
    return False

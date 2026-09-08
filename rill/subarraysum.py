"""Subarrays summing to k: counting them in one pass with prefix sums and a hash.

Counting the contiguous stretches of a series whose values sum to
a target k, how many windows of a signed metric hit an exact
budget, is quadratic by trying every start and end. When the
values are non-negative a two-pointer sweep works, but with
negative values that sweep breaks, because extending a window no
longer only increases the sum, so there is no monotonic edge to
advance. The prefix-sum-and-hash method handles negatives and runs
in one pass. Keep a running prefix sum, and note that a subarray
from just after position i to position j sums to k exactly when the
prefix sum at j minus the prefix sum at i equals k, which is to say
the prefix sum at i equals the current prefix minus k. So maintain
a count of how many times each prefix sum has occurred, and at each
position add the number of earlier positions whose prefix sum was
the current prefix minus k, because each of those marks the start
of a subarray ending here that sums to k. Seeding the count with a
prefix sum of zero seen once handles subarrays that start at the
very beginning. Each element is a constant amount of work, so the
whole count is linear, and it is oblivious to sign because it
reasons about prefix differences rather than window monotonicity.
This module counts the subarrays, checked against a brute-force
over all pairs, so the linear count is correct across negatives as
well as fast.
"""

from __future__ import annotations

from collections import defaultdict

from rill.errors import Invalid


def count_with_sum(values: list[int], target: int) -> int:
    if values is None:
        raise Invalid("values must not be None")
    seen: dict[int, int] = defaultdict(int)
    seen[0] = 1
    prefix = 0
    count = 0
    for value in values:
        prefix += value
        count += seen[prefix - target]
        seen[prefix] += 1
    return count

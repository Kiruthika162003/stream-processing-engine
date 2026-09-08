"""Maximum product subarray: track the running minimum too, because a negative flips it.

Kadane finds the maximum-sum contiguous subarray by keeping one
running best, and the naive instinct is to do the same for the
maximum product, keep the best product ending here and extend or
restart. It is wrong, and the reason is the sign. A large negative
running product is not useless; the next negative value multiplies
it into a large positive, so the smallest product ending at a
position is as important to remember as the largest, because
either can become the maximum after one more element depending on
that element's sign. So the sweep carries both a running maximum
and a running minimum, and at each element the new maximum is the
largest of the element alone, the element times the old maximum,
and the element times the old minimum, with the new minimum the
smallest of the same three. The element-alone term handles the
restart, and including the element-times-old-minimum term is
exactly the case a sum-based Kadane never needs and a product must
have, because multiplying two negatives is the move that turns the
worst running product into the best. Zeros reset both running
values, since any product through a zero is zero. This module
sweeps once tracking both extremes, checked against a brute-force
over all subarrays, so the min-tracking that the naive
single-best version omits is a measured correction.
"""

from __future__ import annotations

from rill.errors import Invalid


def max_product(values: list[int]) -> int:
    if not values:
        raise Invalid("empty series")
    best = current_max = current_min = values[0]
    for value in values[1:]:
        candidates = (value, value * current_max, value * current_min)
        current_max = max(candidates)
        current_min = min(candidates)
        best = max(best, current_max)
    return best

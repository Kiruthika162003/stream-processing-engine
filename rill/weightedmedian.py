"""Weighted median: the point that balances weight, not count, on each side.

The plain median minimizes the total absolute distance to a set of
points, which makes it the best single meeting place when every
point counts equally. Weight the points, though, by demand, by
traffic, by how many requests each location serves, and the plain
median is wrong, because it balances the count of points on each
side rather than the weight. The weighted median is the value
where the total weight at or below it and the total weight at or
above it each reach at least half the total weight, and it is the
point that minimizes the sum of weight times distance, the optimal
placement for a facility serving weighted demand. Finding it is a
sort by value and a walk accumulating weight until the running sum
crosses half the total; the value at that crossing is the answer.
The distinction from the plain median is the one that matters in
practice: a handful of heavily weighted points pull the optimal
location toward them, and treating them as one point each, the
plain median, lands the facility in the wrong place, minimizing
the wrong quantity. This module computes the weighted median and,
to make the claim concrete, exposes the weighted deviation so a
test can confirm the returned point beats its neighbors, so the
balances-weight-not-count property is measured rather than
asserted.
"""

from __future__ import annotations

from rill.errors import Invalid


def weighted_median(items: list[tuple[int, int]]) -> int:
    if not items:
        raise Invalid("no items")
    if any(weight <= 0 for _, weight in items):
        raise Invalid("weights must be positive")
    ordered = sorted(items)
    total = sum(weight for _, weight in ordered)
    running = 0
    for value, weight in ordered:
        running += weight
        if running * 2 >= total:
            return value
    return ordered[-1][0]


def weighted_deviation(items: list[tuple[int, int]], point: int) -> int:
    return sum(weight * abs(value - point) for value, weight in items)

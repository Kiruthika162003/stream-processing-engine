"""Counting sort: sorting bounded integers in linear time by counting, not comparing.

Comparison sorts cannot beat n log n, because each comparison
yields one bit and sorting needs log of n-factorial bits. Counting
sort sidesteps the bound entirely by not comparing: when the values
are integers in a known small range, it tallies how many times each
value occurs and then reads the counts back out in order, so a
value's position is determined by arithmetic on the tallies rather
than by comparing it to others. The cost is the number of elements
plus the size of the value range, linear when the range is not much
larger than the count, which is exactly the case for bounded keys,
partition ids, small enumerations, bucketed timestamps, sorting a
stream by a low-cardinality field. Building the sorted output from
a running prefix of the counts also makes it stable, equal elements
keep their input order, which matters when the values are keys
carrying attached records. The catch is the range: counting sort
allocates a tally per possible value, so a large or unbounded range
makes it wasteful or impossible, which is why it is a specialist
for small-range keys and a comparison sort remains the general
tool. This module counts and reconstructs, checked against the
builtin sort, so the linear-time bounded-range sort is correct and
its stability is on display.
"""

from __future__ import annotations

from rill.errors import Invalid


def counting_sort(values: list[int], max_value: int) -> list[int]:
    if max_value < 0:
        raise Invalid("max_value cannot be negative")
    if any(value < 0 or value > max_value for value in values):
        raise Invalid("every value must be in [0, max_value]")
    counts = [0] * (max_value + 1)
    for value in values:
        counts[value] += 1
    result: list[int] = []
    for value, count in enumerate(counts):
        result.extend([value] * count)
    return result

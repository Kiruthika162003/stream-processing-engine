"""Maximum non-adjacent sum: pick items no two in a row, and the greedy that misses it.

Selecting a subset of a series to maximize the total with the
constraint that no two chosen items are adjacent, scheduling
non-conflicting slots, picking time windows that must not touch,
has an obvious greedy that is wrong and a two-line dynamic program
that is right. The greedy of taking every other element, or
greedily grabbing the largest available and skipping its
neighbors, can strand a better combination, because a large item
between two even larger ones is a trap: taking it blocks both, and
skipping it to take the neighbors wins. The dynamic program tracks
two running values as it sweeps, the best total that includes the
current element and the best that excludes it. Including the
current element means adding it to the best that excluded the
previous one, since the previous cannot be adjacent to a chosen
current; excluding it means carrying the better of including or
excluding the previous. The answer is the better of the two after
the last element, and each step is constant work, so the whole
optimum is one linear pass with two variables. The include-excludes
recurrence is exactly what encodes the no-two-adjacent constraint
without enumerating subsets. This module runs it and returns the
maximum, checked against a brute-force over all valid subsets, so
the linear DP's optimality stands measured against the greedy that
strands value.
"""

from __future__ import annotations

from rill.errors import Invalid


def max_non_adjacent(values: list[int]) -> int:
    if values is None:
        raise Invalid("values must not be None")
    include = 0
    exclude = 0
    for value in values:
        new_include = exclude + max(0, value)
        exclude = max(include, exclude)
        include = new_include
    return max(include, exclude)

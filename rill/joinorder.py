"""Join order: the parenthesization of a chain of joins whose cost the naive order gets wrong.

Joining a chain of relations, or equivalently multiplying a chain
of matrices, is associative in result and wildly non-associative
in cost, because the size of each intermediate result depends on
the order the joins are done, and a badly ordered chain
materializes a huge intermediate that a good order never forms.
The cost of one join in a chain of dimensions is the product of
the three dimensions it touches, so the whole chain's cost is the
sum over the joins in whatever order they are parenthesized, and
that sum can differ by orders of magnitude between orders. The
naive left-to-right order, join the first two then fold in the
next and so on, is often far from best, because it can build a
large intermediate early and then drag it through the rest. The
dynamic program finds the optimum by computing, for every
contiguous sub-chain, the cheapest cost to join it, splitting at
each possible point and taking the split whose two halves plus the
join between them cost least, built up from single relations. This
is the query planner's job for a chain of joins, choosing the
parenthesization before executing, and getting it wrong is how a
query that should be instant runs for minutes. This module
computes the optimal cost and the naive left-to-right cost, so the
gap the ordering makes is a measured number.
"""

from __future__ import annotations

from rill.errors import Invalid


def optimal_cost(dims: list[int]) -> int:
    if len(dims) < 2:
        raise Invalid("need at least two dimensions (one relation)")
    if any(d <= 0 for d in dims):
        raise Invalid("dimensions must be positive")
    n = len(dims) - 1
    best = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            best[i][j] = min(
                best[i][k]
                + best[k + 1][j]
                + dims[i] * dims[k + 1] * dims[j + 1]
                for k in range(i, j)
            )
    return best[0][n - 1]


def left_to_right_cost(dims: list[int]) -> int:
    if len(dims) < 2:
        raise Invalid("need at least two dimensions")
    total = 0
    for index in range(1, len(dims) - 1):
        total += dims[0] * dims[index] * dims[index + 1]
    return total

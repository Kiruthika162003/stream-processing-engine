"""Hungarian algorithm: the cheapest one-to-one assignment of workers to jobs.

Given a square cost matrix, where entry i, j is the cost of giving
job j to worker i, the assignment problem asks for the one-to-one
matching, each worker exactly one job, minimizing the total cost.
Trying every matching is factorial. The Hungarian algorithm solves
it in cubic time by maintaining a pair of potentials, one per row and
one per column, that stay dual-feasible: every potential-pair sums to
at most its cell's cost. It grows a matching one job at a time, and
for each new job it runs a shortest-augmenting-path search over the
reduced costs, the cell cost minus the two potentials, which are
non-negative under feasibility so the search is a Dijkstra-style
relaxation. When the path reaches an unmatched worker it flips the
matching along it, adding one matched pair, and it adjusts the
potentials by the search's minimum slack so feasibility is preserved
and progress is locked in. After all jobs are added the matching is
both complete and optimal, because complementary slackness, every
matched cell having zero reduced cost under a feasible potential, is
exactly the optimality certificate for the linear program the
assignment is. The finding worth stating is that the potentials turn
a factorial search into n shortest-path computations, and the same
duality that proves the answer optimal is what the algorithm
maintains as it runs. This module returns the minimum total cost and
an optimal assignment, and a test checks the cost against the brute
minimum over all permutations for small matrices, so the cubic
method is confirmed to find the true optimum.
"""

from __future__ import annotations

from rill.errors import Invalid

_INF = float("inf")


def solve(cost: list[list[float]]) -> tuple[float, list[int]]:
    if cost is None:
        raise Invalid("cost matrix must not be None")
    n = len(cost)
    if any(len(row) != n for row in cost):
        raise Invalid("cost matrix must be square")
    if n == 0:
        return 0.0, []
    # potentials u (rows) and v (columns), 1-indexed with a sentinel slot
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    match_col = [0] * (n + 1)  # which row is matched to each column
    for i in range(1, n + 1):
        match_col[0] = i
        j0 = 0
        min_slack = [_INF] * (n + 1)
        prev = [-1] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = match_col[j0]
            delta = _INF
            j1 = -1
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < min_slack[j]:
                        min_slack[j] = cur
                        prev[j] = j0
                    if min_slack[j] < delta:
                        delta = min_slack[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[match_col[j]] += delta
                    v[j] -= delta
                else:
                    min_slack[j] -= delta
            j0 = j1
            if match_col[j0] == 0:
                break
        while j0 != 0:
            j1 = prev[j0]
            match_col[j0] = match_col[j1]
            j0 = j1
    assignment = [0] * n
    for j in range(1, n + 1):
        if match_col[j] != 0:
            assignment[match_col[j] - 1] = j - 1
    total = sum(cost[i][assignment[i]] for i in range(n))
    return total, assignment

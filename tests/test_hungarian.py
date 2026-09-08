from __future__ import annotations

import random
from itertools import permutations

import pytest

from rill.errors import Invalid
from rill.hungarian import solve


def _brute(cost):
    n = len(cost)
    best = float("inf")
    for p in permutations(range(n)):
        c = sum(cost[i][p[i]] for i in range(n))
        best = min(best, c)
    return best


class TestAssignment:
    def test_a_concrete_matrix(self):
        cost = [[4, 1, 3], [2, 0, 5], [3, 2, 2]]
        total, assignment = solve(cost)
        assert total == 5
        assert sorted(assignment) == [0, 1, 2]
        assert sum(cost[i][assignment[i]] for i in range(3)) == total

    def test_the_cost_matches_brute_over_all_permutations(self):
        rng = random.Random(67)
        for _ in range(3000):
            n = rng.randint(1, 6)
            cost = [[rng.randint(0, 20) for _ in range(n)] for _ in range(n)]
            total, assignment = solve(cost)
            assert sorted(assignment) == list(range(n))
            assert total == _brute(cost)
            assert sum(cost[i][assignment[i]] for i in range(n)) == total

    def test_the_identity_optimum(self):
        cost = [[0, 9, 9], [9, 0, 9], [9, 9, 0]]
        total, assignment = solve(cost)
        assert total == 0
        assert assignment == [0, 1, 2]

    def test_empty_matrix(self):
        assert solve([]) == (0.0, [])


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            solve(None)

    def test_a_non_square_matrix_is_refused(self):
        with pytest.raises(Invalid):
            solve([[1, 2, 3], [4, 5, 6]])

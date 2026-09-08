from __future__ import annotations

import itertools
import random

import pytest

from rill.errors import Invalid
from rill.nonadjacent import max_non_adjacent


def _brute(values: list[int]) -> int:
    best = 0
    n = len(values)
    for size in range(n + 1):
        for combo in itertools.combinations(range(n), size):
            if all(combo[i + 1] - combo[i] > 1 for i in range(len(combo) - 1)):
                best = max(best, sum(values[i] for i in combo))
    return best


class TestOptimality:
    def test_the_trap_where_the_middle_blocks_both_ends(self):
        # taking the 1 would block both 2s; skipping it wins
        assert max_non_adjacent([2, 1, 2]) == 4

    def test_a_concrete_case(self):
        assert max_non_adjacent([3, 2, 7, 10]) == 13

    def test_it_matches_brute_force(self):
        rng = random.Random(4)
        for _ in range(500):
            values = [rng.randint(-5, 10) for _ in range(rng.randint(0, 12))]
            assert max_non_adjacent(values) == _brute(values)


class TestEdges:
    def test_all_negative_takes_nothing(self):
        assert max_non_adjacent([-1, -2, -3]) == 0

    def test_empty_is_zero(self):
        assert max_non_adjacent([]) == 0


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            max_non_adjacent(None)

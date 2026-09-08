from __future__ import annotations

import itertools
import random

import pytest

from rill.errors import Invalid
from rill.knapsack import greedy_density, knapsack


def _brute(items: list[tuple[int, int]], capacity: int) -> int:
    best = 0
    for size in range(len(items) + 1):
        for combo in itertools.combinations(items, size):
            if sum(weight for weight, _ in combo) <= capacity:
                best = max(best, sum(value for _, value in combo))
    return best


class TestGreedyLoses:
    def test_dp_beats_the_density_greedy_on_the_classic_case(self):
        items = [(10, 60), (20, 100), (30, 120)]
        assert knapsack(items, 50) == 220
        assert greedy_density(items, 50) == 160


class TestCorrectness:
    def test_it_matches_brute_force(self):
        rng = random.Random(4)
        for _ in range(300):
            count = rng.randint(1, 8)
            items = [
                (rng.randint(1, 8), rng.randint(1, 10)) for _ in range(count)
            ]
            capacity = rng.randint(0, 15)
            assert knapsack(items, capacity) == _brute(items, capacity)

    def test_zero_capacity_holds_nothing(self):
        assert knapsack([(1, 5)], 0) == 0

    def test_no_items_is_zero(self):
        assert knapsack([], 10) == 0


class TestRefusals:
    def test_a_negative_capacity_is_refused(self):
        with pytest.raises(Invalid):
            knapsack([(1, 1)], -1)

    def test_a_negative_weight_is_refused(self):
        with pytest.raises(Invalid):
            knapsack([(-1, 1)], 5)

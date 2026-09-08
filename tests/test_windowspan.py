from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.windowspan import longest_within_budget


def _brute(values: list[int], budget: int) -> int:
    best = 0
    for i in range(len(values)):
        running = 0
        for j in range(i, len(values)):
            running += values[j]
            if running <= budget:
                best = max(best, j - i + 1)
    return best


class TestCorrectness:
    def test_it_matches_brute_force_over_random_series(self):
        rng = random.Random(6)
        for _ in range(500):
            size = rng.randint(1, 20)
            values = [rng.randint(0, 10) for _ in range(size)]
            budget = rng.randint(0, 30)
            assert longest_within_budget(values, budget)[0] == _brute(
                values, budget
            )

    def test_a_concrete_window(self):
        assert longest_within_budget([1, 2, 3, 4, 5], 6) == (3, 0)


class TestEdges:
    def test_all_zeros_fit_any_budget(self):
        assert longest_within_budget([0, 0, 0], 0) == (3, 0)

    def test_a_budget_too_small_for_any_element_finds_nothing(self):
        assert longest_within_budget([5, 6, 7], 3) == (0, 0)


class TestRefusals:
    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            longest_within_budget([1, -2, 3], 5)

    def test_a_negative_budget_is_refused(self):
        with pytest.raises(Invalid):
            longest_within_budget([1], -1)

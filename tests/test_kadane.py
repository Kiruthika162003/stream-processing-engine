from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.kadane import max_subarray


def _brute(values: list[int]) -> int:
    best = values[0]
    for i in range(len(values)):
        running = 0
        for j in range(i, len(values)):
            running += values[j]
            best = max(best, running)
    return best


class TestCorrectness:
    def test_it_matches_brute_force_over_random_series(self):
        rng = random.Random(4)
        for _ in range(500):
            size = rng.randint(1, 20)
            values = [rng.randint(-10, 10) for _ in range(size)]
            assert max_subarray(values)[0] == _brute(values)

    def test_the_classic_example(self):
        total, lo, hi = max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4])
        assert total == 6
        assert (lo, hi) == (3, 6)


class TestAllNegative:
    def test_all_negative_returns_the_least_negative_element(self):
        total, lo, hi = max_subarray([-5, -2, -8])
        assert total == -2
        assert (lo, hi) == (1, 1)

    def test_a_single_element_is_its_own_window(self):
        assert max_subarray([7]) == (7, 0, 0)


class TestRefusals:
    def test_an_empty_series_is_refused(self):
        with pytest.raises(Invalid):
            max_subarray([])

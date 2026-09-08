from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.maxproduct import max_product


def _brute(values: list[int]) -> int:
    best = values[0]
    for i in range(len(values)):
        product = 1
        for j in range(i, len(values)):
            product *= values[j]
            best = max(best, product)
    return best


class TestCorrectness:
    def test_it_matches_brute_force(self):
        rng = random.Random(5)
        for _ in range(500):
            values = [rng.randint(-5, 5) for _ in range(rng.randint(1, 12))]
            assert max_product(values) == _brute(values)

    def test_a_simple_case(self):
        assert max_product([2, 3, -2, 4]) == 6


class TestSigns:
    def test_two_negatives_multiply_to_the_maximum(self):
        assert max_product([-2, 3, -4]) == 24

    def test_a_zero_resets_the_running_products(self):
        assert max_product([-2, 0, -1]) == 0

    def test_a_single_element(self):
        assert max_product([-7]) == -7


class TestRefusals:
    def test_an_empty_series_is_refused(self):
        with pytest.raises(Invalid):
            max_product([])

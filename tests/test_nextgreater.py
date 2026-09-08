from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.nextgreater import next_greater_distances


def _brute(values: list[int]) -> list[int]:
    out = [-1] * len(values)
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[j] > values[i]:
                out[i] = j - i
                break
    return out


class TestCorrectness:
    def test_it_matches_brute_force_over_random_series(self):
        rng = random.Random(5)
        for _ in range(500):
            size = rng.randint(1, 20)
            values = [rng.randint(0, 20) for _ in range(size)]
            assert next_greater_distances(values) == _brute(values)

    def test_a_concrete_series(self):
        assert next_greater_distances([3, 1, 4, 1, 5]) == [2, 1, 2, 1, -1]


class TestEdges:
    def test_a_descending_series_finds_nothing_greater(self):
        assert next_greater_distances([5, 4, 3]) == [-1, -1, -1]

    def test_equal_values_do_not_count_as_greater(self):
        assert next_greater_distances([2, 2, 2]) == [-1, -1, -1]


class TestRefusals:
    def test_an_empty_series_is_refused(self):
        with pytest.raises(Invalid):
            next_greater_distances([])

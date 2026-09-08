from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.lis import lis_length


def _dp(values: list[int]) -> int:
    if not values:
        return 0
    best = [1] * len(values)
    for i in range(len(values)):
        for j in range(i):
            if values[j] < values[i]:
                best[i] = max(best[i], best[j] + 1)
    return max(best)


class TestCorrectness:
    def test_it_matches_the_dynamic_program(self):
        rng = random.Random(8)
        for _ in range(500):
            size = rng.randint(1, 25)
            values = [rng.randint(0, 20) for _ in range(size)]
            assert lis_length(values) == _dp(values)

    def test_a_concrete_series(self):
        assert lis_length([10, 9, 2, 5, 3, 7, 101, 18]) == 4


class TestEdges:
    def test_a_sorted_series_is_all_increasing(self):
        assert lis_length([1, 2, 3, 4]) == 4

    def test_a_descending_series_has_length_one(self):
        assert lis_length([4, 3, 2, 1]) == 1

    def test_ties_do_not_extend_a_strictly_increasing_run(self):
        assert lis_length([2, 2, 2]) == 1


class TestRefusals:
    def test_an_empty_series_is_refused(self):
        with pytest.raises(Invalid):
            lis_length([])

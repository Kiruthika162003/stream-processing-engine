from __future__ import annotations

import functools
import random

import pytest

from rill.errors import Invalid
from rill.joinorder import left_to_right_cost, optimal_cost


@functools.lru_cache(None)
def _brute(dims: tuple[int, ...], i: int, j: int) -> int:
    if i == j:
        return 0
    return min(
        _brute(dims, i, k)
        + _brute(dims, k + 1, j)
        + dims[i] * dims[k + 1] * dims[j + 1]
        for k in range(i, j)
    )


class TestOptimality:
    def test_optimal_beats_left_to_right(self):
        dims = [40, 20, 30, 10, 30]
        assert optimal_cost(dims) == 26000
        assert left_to_right_cost(dims) == 48000

    def test_it_matches_brute_force(self):
        rng = random.Random(3)
        for _ in range(300):
            dims = tuple(rng.randint(1, 50) for _ in range(rng.randint(2, 7)))
            assert optimal_cost(list(dims)) == _brute(dims, 0, len(dims) - 2)


class TestEdges:
    def test_a_single_join_has_one_cost(self):
        assert optimal_cost([2, 3, 4]) == 2 * 3 * 4


class TestRefusals:
    def test_too_few_dimensions_is_refused(self):
        with pytest.raises(Invalid):
            optimal_cost([5])

    def test_a_nonpositive_dimension_is_refused(self):
        with pytest.raises(Invalid):
            optimal_cost([2, 0, 3])

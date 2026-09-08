from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.rainwater import trapped_water


def _brute(heights: list[int]) -> int:
    total = 0
    for i in range(len(heights)):
        left_max = max(heights[: i + 1])
        right_max = max(heights[i:])
        total += min(left_max, right_max) - heights[i]
    return total


class TestCorrectness:
    def test_the_classic_profile(self):
        assert trapped_water([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6

    def test_it_matches_brute_force(self):
        rng = random.Random(7)
        for _ in range(500):
            heights = [rng.randint(0, 10) for _ in range(rng.randint(1, 15))]
            assert trapped_water(heights) == _brute(heights)


class TestEdges:
    def test_a_monotonic_profile_traps_nothing(self):
        assert trapped_water([1, 2, 3, 4]) == 0
        assert trapped_water([4, 3, 2, 1]) == 0

    def test_a_single_valley(self):
        assert trapped_water([3, 0, 3]) == 3

    def test_empty_traps_nothing(self):
        assert trapped_water([]) == 0


class TestRefusals:
    def test_a_negative_height_is_refused(self):
        with pytest.raises(Invalid):
            trapped_water([1, -1, 2])

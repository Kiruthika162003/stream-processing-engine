from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.maxrectangle import largest_rectangle


def _brute(heights: list[int]) -> int:
    best = 0
    for i in range(len(heights)):
        floor = heights[i]
        for j in range(i, len(heights)):
            floor = min(floor, heights[j])
            best = max(best, floor * (j - i + 1))
    return best


class TestCorrectness:
    def test_the_classic_histogram(self):
        assert largest_rectangle([2, 1, 5, 6, 2, 3]) == 10

    def test_it_matches_brute_force(self):
        rng = random.Random(6)
        for _ in range(500):
            heights = [rng.randint(0, 10) for _ in range(rng.randint(1, 15))]
            assert largest_rectangle(heights) == _brute(heights)


class TestEdges:
    def test_uniform_bars_fill_the_whole_width(self):
        assert largest_rectangle([4, 4, 4]) == 12

    def test_a_single_bar_is_its_own_area(self):
        assert largest_rectangle([7]) == 7

    def test_no_bars_is_zero(self):
        assert largest_rectangle([]) == 0


class TestRefusals:
    def test_a_negative_height_is_refused(self):
        with pytest.raises(Invalid):
            largest_rectangle([1, -2, 3])

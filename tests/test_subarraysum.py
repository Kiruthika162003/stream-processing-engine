from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.subarraysum import count_with_sum


def _brute(values: list[int], target: int) -> int:
    count = 0
    for i in range(len(values)):
        running = 0
        for j in range(i, len(values)):
            running += values[j]
            if running == target:
                count += 1
    return count


class TestCounting:
    def test_a_simple_case(self):
        assert count_with_sum([1, 1, 1], 2) == 2

    def test_it_handles_negatives_a_two_pointer_could_not(self):
        # [1,-1], [0], and [1,-1,0] all sum to zero
        assert count_with_sum([1, -1, 0], 0) == 3

    def test_it_matches_brute_force_with_negatives(self):
        rng = random.Random(7)
        for _ in range(500):
            values = [rng.randint(-5, 5) for _ in range(rng.randint(0, 15))]
            target = rng.randint(-10, 10)
            assert count_with_sum(values, target) == _brute(values, target)


class TestEdges:
    def test_no_matching_subarray_is_zero(self):
        assert count_with_sum([1, 2, 3], 100) == 0

    def test_an_empty_series_counts_nothing(self):
        assert count_with_sum([], 0) == 0


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            count_with_sum(None, 0)

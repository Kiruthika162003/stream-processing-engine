from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.inversions import count_inversions


def _brute(values: list[int]) -> int:
    return sum(
        1
        for i in range(len(values))
        for j in range(i + 1, len(values))
        if values[i] > values[j]
    )


class TestCounting:
    def test_a_sorted_sequence_has_no_inversions(self):
        assert count_inversions([1, 2, 3, 4]) == 0

    def test_a_reversed_sequence_is_maximally_disordered(self):
        assert count_inversions([4, 3, 2, 1]) == 6  # 4 choose 2

    def test_a_concrete_case(self):
        assert count_inversions([2, 4, 1, 3, 5]) == 3

    def test_it_matches_brute_force(self):
        rng = random.Random(3)
        for _ in range(500):
            values = [rng.randint(0, 20) for _ in range(rng.randint(0, 15))]
            assert count_inversions(values) == _brute(values)


class TestEdges:
    def test_empty_and_single_have_no_inversions(self):
        assert count_inversions([]) == 0
        assert count_inversions([7]) == 0

    def test_duplicates_are_not_inversions(self):
        assert count_inversions([3, 3, 3]) == 0


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            count_inversions(None)

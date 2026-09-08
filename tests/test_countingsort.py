from __future__ import annotations

import random

import pytest

from rill.countingsort import counting_sort
from rill.errors import Invalid


class TestCorrectness:
    def test_a_concrete_case(self):
        assert counting_sort([3, 1, 4, 1, 5, 9, 2, 6], 9) == [1, 1, 2, 3, 4, 5, 6, 9]

    def test_it_matches_the_builtin_sort(self):
        rng = random.Random(3)
        for _ in range(500):
            values = [rng.randint(0, 20) for _ in range(rng.randint(0, 30))]
            assert counting_sort(values, 20) == sorted(values)

    def test_empty_stays_empty(self):
        assert counting_sort([], 10) == []

    def test_duplicates_are_kept(self):
        assert counting_sort([2, 2, 1, 1, 0], 2) == [0, 1, 1, 2, 2]


class TestRefusals:
    def test_a_value_above_the_max_is_refused(self):
        with pytest.raises(Invalid):
            counting_sort([1, 11], 10)

    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            counting_sort([-1], 10)

    def test_a_negative_max_is_refused(self):
        with pytest.raises(Invalid):
            counting_sort([], -1)

from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.heapsort import heap_sort


class TestCorrectness:
    def test_a_concrete_case(self):
        assert heap_sort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

    def test_it_matches_the_builtin_sort(self):
        rng = random.Random(5)
        for _ in range(500):
            values = [rng.randint(-50, 50) for _ in range(rng.randint(0, 30))]
            assert heap_sort(values) == sorted(values)

    def test_negatives_and_duplicates(self):
        assert heap_sort([-3, 0, -3, 2, 2]) == [-3, -3, 0, 2, 2]


class TestEdges:
    def test_empty_and_single(self):
        assert heap_sort([]) == []
        assert heap_sort([7]) == [7]

    def test_it_does_not_mutate_the_input(self):
        original = [3, 1, 2]
        heap_sort(original)
        assert original == [3, 1, 2]


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            heap_sort(None)

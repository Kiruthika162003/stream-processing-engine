from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.quickselect import select


class TestCorrectness:
    def test_it_matches_a_full_sort_across_random_trials(self):
        rng = random.Random(3)
        for _ in range(200):
            size = rng.randint(1, 60)
            data = [rng.randint(0, 100) for _ in range(size)]
            k = rng.randint(0, size - 1)
            assert select(data, k) == sorted(data)[k]

    def test_the_ends_are_the_min_and_the_max(self):
        data = [3, 1, 4, 1, 5, 9, 2, 6]
        assert select(data, 0) == 1
        assert select(data, len(data) - 1) == 9

    def test_it_handles_duplicates(self):
        data = [5, 5, 5, 1, 5]
        assert select(data, 0) == 1
        assert select(data, 4) == 5

    def test_it_does_not_mutate_the_input(self):
        data = [3, 1, 2]
        select(data, 1)
        assert data == [3, 1, 2]


class TestRefusals:
    def test_an_empty_sequence_is_refused(self):
        with pytest.raises(Invalid):
            select([], 0)

    def test_a_rank_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            select([1, 2, 3], 5)

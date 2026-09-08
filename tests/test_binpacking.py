from __future__ import annotations

import random

import pytest

from rill.binpacking import first_fit, first_fit_decreasing
from rill.errors import Invalid


class TestDecreasingWins:
    def test_ffd_packs_tighter_than_small_first(self):
        items = [2, 5, 4, 7, 1, 3, 8]
        small_first = first_fit(sorted(items), 10)
        assert small_first == 4
        assert first_fit_decreasing(items, 10) == 3  # the optimum

    def test_ffd_never_loses_to_first_fit_on_random_items(self):
        rng = random.Random(2)
        items = [rng.randint(1, 10) for _ in range(50)]
        assert first_fit_decreasing(items, 10) <= first_fit(items, 10)


class TestLowerBound:
    def test_the_bins_are_at_least_the_total_over_capacity(self):
        items = [6, 6, 6, 6]
        lower = -(-sum(items) // 10)
        assert first_fit_decreasing(items, 10) >= lower


class TestRefusals:
    def test_an_item_larger_than_a_bin_is_refused(self):
        with pytest.raises(Invalid):
            first_fit([11], 10)

    def test_a_nonpositive_capacity_is_refused(self):
        with pytest.raises(Invalid):
            first_fit_decreasing([1], 0)

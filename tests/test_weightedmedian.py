from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.weightedmedian import weighted_deviation, weighted_median


class TestWeighting:
    def test_a_heavy_point_pulls_the_median_toward_it(self):
        items = [(1, 1), (2, 1), (3, 10)]
        # plain median of positions would be 2; weight pulls it to 3
        assert weighted_median(items) == 3

    def test_uniform_weights_give_the_plain_median(self):
        items = [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1)]
        assert weighted_median(items) == 3

    def test_a_single_item_is_its_own_median(self):
        assert weighted_median([(7, 5)]) == 7


class TestOptimality:
    def test_it_minimizes_the_weighted_deviation(self):
        rng = random.Random(3)
        for _ in range(500):
            items = [
                (rng.randint(0, 20), rng.randint(1, 10))
                for _ in range(rng.randint(1, 8))
            ]
            median = weighted_median(items)
            best = weighted_deviation(items, median)
            assert all(weighted_deviation(items, v) >= best for v in range(21))


class TestRefusals:
    def test_no_items_is_refused(self):
        with pytest.raises(Invalid):
            weighted_median([])

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            weighted_median([(1, 0)])

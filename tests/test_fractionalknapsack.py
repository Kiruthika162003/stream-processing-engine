from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.fractionalknapsack import max_value
from rill.knapsack import knapsack


class TestGreedyIsOptimal:
    def test_fractional_beats_zero_one_on_the_same_items(self):
        items = [(10, 60), (20, 100), (30, 120)]
        # fractional can take part of the third item where 0/1 cannot
        assert max_value(items, 50) == 240.0
        assert knapsack(items, 50) == 220

    def test_a_partial_item_yields_a_proportional_value(self):
        assert max_value([(10, 60)], 5) == 30.0


class TestEdges:
    def test_everything_fitting_takes_all_the_value(self):
        assert max_value([(2, 10), (3, 20)], 100) == 30.0

    def test_zero_capacity_takes_nothing(self):
        assert max_value([(1, 5)], 0) == 0.0


class TestRefusals:
    def test_a_negative_capacity_is_refused(self):
        with pytest.raises(Invalid):
            max_value([(1, 1)], -1)

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            max_value([(0, 5)], 10)

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.maxminfair import max_min_fair


class TestFairness:
    def test_a_small_demand_frees_capacity_for_the_large_ones(self):
        # equal split would be 4 each; the demand of 2 hands back 2
        assert max_min_fair([2, 10, 10], 12) == [2, 5, 5]

    def test_two_small_demands_leave_the_rest_to_the_big_one(self):
        assert max_min_fair([1, 1, 100], 12) == [1, 1, 10]

    def test_scarce_capacity_splits_equally(self):
        assert max_min_fair([5, 5, 5], 9) == [3, 3, 3]

    def test_ample_capacity_satisfies_everyone(self):
        assert max_min_fair([2, 3], 10) == [2, 3]

    def test_the_allocation_never_exceeds_the_capacity(self):
        allocation = max_min_fair([7, 7, 7], 10)
        assert sum(allocation) <= 10


class TestRefusals:
    def test_no_demands_is_refused(self):
        with pytest.raises(Invalid):
            max_min_fair([], 10)

    def test_a_negative_demand_is_refused(self):
        with pytest.raises(Invalid):
            max_min_fair([-1], 10)

    def test_a_negative_capacity_is_refused(self):
        with pytest.raises(Invalid):
            max_min_fair([1], -5)

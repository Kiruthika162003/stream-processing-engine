from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.prefixsum import PrefixSum


class TestRangeSum:
    def test_a_range_is_one_prefix_minus_another(self):
        prefix = PrefixSum([1, 2, 3, 4, 5])
        assert prefix.range_sum(1, 4) == 2 + 3 + 4

    def test_the_full_range_is_the_total(self):
        prefix = PrefixSum([1, 2, 3, 4, 5])
        assert prefix.range_sum(0, 5) == 15
        assert prefix.total() == 15

    def test_an_empty_range_is_zero(self):
        prefix = PrefixSum([1, 2, 3])
        assert prefix.range_sum(2, 2) == 0

    def test_it_matches_a_direct_sum_everywhere(self):
        values = [4, 1, 9, 2, 7, 3]
        prefix = PrefixSum(values)
        for lo in range(len(values) + 1):
            for hi in range(lo, len(values) + 1):
                assert prefix.range_sum(lo, hi) == sum(values[lo:hi])


class TestRefusals:
    def test_a_range_out_of_bounds_is_refused(self):
        with pytest.raises(Invalid):
            PrefixSum([1, 2, 3]).range_sum(0, 9)

    def test_an_inverted_range_is_refused(self):
        with pytest.raises(Invalid):
            PrefixSum([1, 2, 3]).range_sum(2, 1)

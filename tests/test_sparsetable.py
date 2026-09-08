from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.sparsetable import SparseTable


class TestRangeMin:
    def test_it_matches_brute_force_over_random_tables(self):
        rng = random.Random(7)
        for _ in range(300):
            size = rng.randint(1, 40)
            values = [rng.randint(-50, 50) for _ in range(size)]
            table = SparseTable(values)
            for _ in range(10):
                lo = rng.randint(0, size - 1)
                hi = rng.randint(lo + 1, size)
                assert table.range_min(lo, hi) == min(values[lo:hi])

    def test_a_concrete_range(self):
        table = SparseTable([3, 1, 4, 1, 5, 9, 2, 6])
        assert table.range_min(2, 6) == 1

    def test_a_single_element_range_is_that_element(self):
        table = SparseTable([5, 2, 8])
        assert table.range_min(1, 2) == 2

    def test_the_full_range_is_the_minimum(self):
        table = SparseTable([5, 2, 8, 1, 9])
        assert table.range_min(0, 5) == 1


class TestRefusals:
    def test_building_over_nothing_is_refused(self):
        with pytest.raises(Invalid):
            SparseTable([])

    def test_an_out_of_bounds_range_is_refused(self):
        with pytest.raises(Invalid):
            SparseTable([1, 2, 3]).range_min(0, 9)

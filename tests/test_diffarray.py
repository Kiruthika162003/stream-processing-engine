from __future__ import annotations

import random

import pytest

from rill.diffarray import DifferenceArray
from rill.errors import Invalid


class TestCorrectness:
    def test_it_matches_naive_per_element_application(self):
        rng = random.Random(3)
        for _ in range(300):
            size = rng.randint(1, 30)
            diff = DifferenceArray(size)
            naive = [0] * size
            for _ in range(rng.randint(0, 20)):
                lo = rng.randint(0, size - 1)
                hi = rng.randint(lo, size)
                delta = rng.randint(-5, 5)
                diff.add_range(lo, hi, delta)
                for index in range(lo, hi):
                    naive[index] += delta
            assert diff.materialize() == naive

    def test_overlapping_ranges_accumulate(self):
        diff = DifferenceArray(5)
        diff.add_range(1, 4, 3)
        diff.add_range(0, 2, 1)
        assert diff.materialize() == [1, 4, 3, 3, 0]

    def test_no_updates_is_all_zeros(self):
        assert DifferenceArray(4).materialize() == [0, 0, 0, 0]


class TestRefusals:
    def test_a_nonpositive_size_is_refused(self):
        with pytest.raises(Invalid):
            DifferenceArray(0)

    def test_an_out_of_bounds_range_is_refused(self):
        with pytest.raises(Invalid):
            DifferenceArray(5).add_range(0, 9, 1)

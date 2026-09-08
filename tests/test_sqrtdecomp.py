from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.sqrtdecomp import SqrtDecomposition


class TestRangeSum:
    def test_a_range_sums_its_elements(self):
        sd = SqrtDecomposition([1, 2, 3, 4, 5])
        assert sd.range_sum(1, 3) == 2 + 3 + 4
        assert sd.range_sum(0, 4) == 15

    def test_a_point_update_shows_in_later_sums(self):
        sd = SqrtDecomposition([1, 2, 3, 4, 5])
        sd.update(2, 30)  # was 3
        assert sd.range_sum(0, 4) == 1 + 2 + 30 + 4 + 5

    def test_it_matches_a_naive_array(self):
        rng = random.Random(6)
        for _ in range(300):
            size = rng.randint(1, 40)
            array = [rng.randint(-10, 10) for _ in range(size)]
            sd = SqrtDecomposition(array)
            for _ in range(30):
                if rng.random() < 0.5:
                    index = rng.randrange(size)
                    value = rng.randint(-10, 10)
                    sd.update(index, value)
                    array[index] = value
                else:
                    lo = rng.randrange(size)
                    hi = rng.randint(lo, size - 1)
                    assert sd.range_sum(lo, hi) == sum(array[lo : hi + 1])


class TestRefusals:
    def test_an_empty_array_is_refused(self):
        with pytest.raises(Invalid):
            SqrtDecomposition([])

    def test_an_out_of_range_index_is_refused(self):
        with pytest.raises(Invalid):
            SqrtDecomposition([1, 2, 3]).update(9, 1)

    def test_an_out_of_bounds_range_is_refused(self):
        with pytest.raises(Invalid):
            SqrtDecomposition([1, 2, 3]).range_sum(0, 9)

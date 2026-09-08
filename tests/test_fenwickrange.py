from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.fenwickrange import RangeFenwick


class TestRangeOps:
    def test_a_range_add_shows_in_the_range_sum(self):
        tree = RangeFenwick(size=5)
        tree.add_range(2, 4, 3)  # positions 2, 3, 4 get 3
        assert tree.range_sum(1, 5) == 9
        assert tree.range_sum(2, 2) == 3
        assert tree.range_sum(1, 1) == 0

    def test_overlapping_range_adds_accumulate(self):
        tree = RangeFenwick(size=5)
        tree.add_range(1, 5, 1)
        tree.add_range(3, 4, 10)
        assert tree.range_sum(1, 5) == 5 + 20

    def test_it_matches_a_naive_array(self):
        rng = random.Random(3)
        for _ in range(300):
            size = rng.randint(1, 30)
            tree = RangeFenwick(size)
            naive = [0] * (size + 1)  # 1-based
            for _ in range(rng.randint(1, 30)):
                lo = rng.randint(1, size)
                hi = rng.randint(lo, size)
                if rng.random() < 0.5:
                    delta = rng.randint(-5, 5)
                    tree.add_range(lo, hi, delta)
                    for index in range(lo, hi + 1):
                        naive[index] += delta
                else:
                    assert tree.range_sum(lo, hi) == sum(naive[lo : hi + 1])


class TestRefusals:
    def test_a_nonpositive_size_is_refused(self):
        with pytest.raises(Invalid):
            RangeFenwick(0)

    def test_an_out_of_bounds_range_is_refused(self):
        with pytest.raises(Invalid):
            RangeFenwick(5).add_range(0, 3, 1)

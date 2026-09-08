from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.lazysegtree import LazySegmentTree


class TestRangeOps:
    def test_a_range_add_shows_in_the_range_sum(self):
        tree = LazySegmentTree(size=5)
        tree.add_range(1, 3, 4)
        assert tree.range_sum(0, 4) == 12  # three elements at 4
        assert tree.range_sum(1, 1) == 4
        assert tree.range_sum(0, 0) == 0

    def test_overlapping_range_adds_accumulate(self):
        tree = LazySegmentTree(size=5)
        tree.add_range(0, 4, 1)
        tree.add_range(2, 3, 10)
        assert tree.range_sum(0, 4) == 5 + 20

    def test_it_matches_a_naive_array_over_random_operations(self):
        rng = random.Random(7)
        for _ in range(300):
            size = rng.randint(1, 30)
            tree = LazySegmentTree(size)
            naive = [0] * size
            for _ in range(rng.randint(1, 30)):
                lo = rng.randint(0, size - 1)
                hi = rng.randint(lo, size - 1)
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
            LazySegmentTree(0)

    def test_an_out_of_bounds_range_is_refused(self):
        with pytest.raises(Invalid):
            LazySegmentTree(5).add_range(0, 9, 1)

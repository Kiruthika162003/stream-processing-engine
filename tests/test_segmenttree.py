from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.segmenttree import SegmentTree


class TestRangeMin:
    def test_range_min_matches_brute_force(self):
        rng = random.Random(6)
        size = 256
        tree = SegmentTree(size=size)
        raw = [1 << 60] * size
        for _ in range(2000):
            index = rng.randrange(size)
            value = rng.randint(0, 1000)
            tree.update(index, value)
            raw[index] = value
        for lo, hi in ((0, 256), (10, 50), (100, 101), (200, 256)):
            assert tree.query(lo, hi) == min(raw[lo:hi])

    def test_a_single_element_range_returns_that_element(self):
        tree = SegmentTree(size=8)
        tree.update(3, 42)
        assert tree.query(3, 4) == 42


class TestOtherCombiners:
    def test_it_works_as_a_range_max_tree(self):
        tree = SegmentTree(size=8, identity=-1, combine=max)
        for index, value in enumerate([3, 1, 4, 1, 5, 9, 2, 6]):
            tree.update(index, value)
        assert tree.query(2, 6) == 9


class TestRefusals:
    def test_a_nonpositive_size_is_refused(self):
        with pytest.raises(Invalid):
            SegmentTree(size=0)

    def test_an_out_of_range_update_is_refused(self):
        with pytest.raises(Invalid):
            SegmentTree(size=8).update(8, 1)

    def test_an_invalid_query_range_is_refused(self):
        with pytest.raises(Invalid):
            SegmentTree(size=8).query(5, 2)

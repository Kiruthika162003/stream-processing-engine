from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.intervalset import IntervalSet


class TestMerging:
    def test_disjoint_intervals_stay_separate(self):
        s = IntervalSet()
        s.add(1, 3)
        s.add(5, 7)
        assert s.intervals() == [(1, 3), (5, 7)]

    def test_a_bridging_interval_collapses_three_into_one(self):
        s = IntervalSet()
        s.add(1, 3)
        s.add(5, 7)
        s.add(2, 6)  # bridges the gap
        assert s.intervals() == [(1, 7)]

    def test_a_contained_interval_changes_nothing(self):
        s = IntervalSet()
        s.add(1, 10)
        s.add(3, 5)
        assert s.intervals() == [(1, 10)]


class TestQueries:
    def test_coverage_is_half_open(self):
        s = IntervalSet()
        s.add(1, 7)
        assert s.covers(4)
        assert not s.covers(7)

    def test_total_length_sums_the_disjoint_cover(self):
        s = IntervalSet()
        s.add(1, 3)
        s.add(5, 7)
        assert s.total_length() == 4

    def test_it_matches_a_point_set_model(self):
        rng = random.Random(4)
        for _ in range(300):
            s = IntervalSet()
            covered: set[int] = set()
            for _ in range(rng.randint(0, 15)):
                lo = rng.randint(0, 20)
                hi = lo + rng.randint(0, 5)
                s.add(lo, hi)
                covered.update(range(lo, hi))
            assert s.total_length() == len(covered)
            assert all(s.covers(p) == (p in covered) for p in range(26))


class TestRefusals:
    def test_an_inverted_interval_is_refused(self):
        with pytest.raises(Invalid):
            IntervalSet().add(5, 1)

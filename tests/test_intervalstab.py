from __future__ import annotations

import itertools
import random

import pytest

from rill.errors import Invalid
from rill.intervalstab import min_stab_points


def _brute(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    candidates = sorted({e for _, e in intervals} | {s for s, _ in intervals})
    for size in range(1, len(intervals) + 1):
        for combo in itertools.combinations(candidates, size):
            if all(any(s <= p <= e for p in combo) for s, e in intervals):
                return size
    return len(intervals)


class TestGreedy:
    def test_a_concrete_case(self):
        assert min_stab_points([(1, 3), (2, 5), (4, 6)]) == 2

    def test_it_matches_brute_force(self):
        rng = random.Random(4)
        for _ in range(300):
            intervals = []
            for _ in range(rng.randint(0, 6)):
                start = rng.randint(0, 10)
                intervals.append((start, start + rng.randint(0, 5)))
            assert min_stab_points(intervals) == _brute(intervals)


class TestEdges:
    def test_disjoint_intervals_each_need_a_point(self):
        assert min_stab_points([(1, 2), (4, 5), (7, 8)]) == 3

    def test_a_common_overlap_needs_one_point(self):
        assert min_stab_points([(1, 10), (2, 8), (3, 5)]) == 1

    def test_no_intervals_need_no_points(self):
        assert min_stab_points([]) == 0


class TestRefusals:
    def test_an_inverted_interval_is_refused(self):
        with pytest.raises(Invalid):
            min_stab_points([(5, 1)])

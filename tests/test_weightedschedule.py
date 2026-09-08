from __future__ import annotations

import itertools
import random

import pytest

from rill.errors import Invalid
from rill.weightedschedule import greedy_weight, max_weight


def _brute(intervals: list[tuple[int, int, int]]) -> int:
    best = 0
    for size in range(len(intervals) + 1):
        for combo in itertools.combinations(intervals, size):
            ordered = sorted(combo, key=lambda iv: iv[1])
            ok = all(
                ordered[i][0] >= ordered[i - 1][1] for i in range(1, len(ordered))
            )
            if ok:
                best = max(best, sum(weight for _, _, weight in combo))
    return best


class TestGreedyLoses:
    def test_dp_takes_the_valuable_interval_greedy_skips(self):
        intervals = [(0, 3, 1), (3, 6, 1), (6, 9, 1), (0, 9, 10)]
        assert max_weight(intervals) == 10
        assert greedy_weight(intervals) == 3


class TestCorrectness:
    def test_it_matches_brute_force(self):
        rng = random.Random(3)
        for _ in range(300):
            count = rng.randint(1, 8)
            intervals = []
            for _ in range(count):
                start = rng.randint(0, 10)
                end = start + rng.randint(1, 5)
                intervals.append((start, end, rng.randint(1, 10)))
            assert max_weight(intervals) == _brute(intervals)

    def test_empty_is_zero(self):
        assert max_weight([]) == 0

    def test_a_single_interval_is_its_weight(self):
        assert max_weight([(0, 5, 7)]) == 7


class TestRefusals:
    def test_a_negative_weight_is_refused(self):
        with pytest.raises(Invalid):
            max_weight([(0, 5, -1)])

    def test_an_inverted_interval_is_refused(self):
        with pytest.raises(Invalid):
            max_weight([(5, 1, 3)])

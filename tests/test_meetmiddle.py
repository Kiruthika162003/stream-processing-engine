from __future__ import annotations

import random
from itertools import combinations

import pytest

from rill.errors import Invalid
from rill.meetmiddle import subset_sum_reachable


def _brute(items, target):
    return any(
        sum(c) == target
        for r in range(len(items) + 1)
        for c in combinations(items, r)
    )


class TestReachable:
    def test_known_cases(self):
        assert subset_sum_reachable([3, 5, 8], 0) is True  # empty subset
        assert subset_sum_reachable([3, 5, 8], 13) is True  # 5 + 8
        assert subset_sum_reachable([3, 5, 8], 4) is False

    def test_negatives_are_handled(self):
        assert subset_sum_reachable([-4, 6, -2], 2) is True  # -4 + 6
        assert subset_sum_reachable([-4, 6, -2], 100) is False

    def test_it_matches_brute_enumeration(self):
        rng = random.Random(71)
        for _ in range(5000):
            n = rng.randint(0, 12)
            items = [rng.randint(-15, 15) for _ in range(n)]
            target = rng.randint(-40, 40)
            assert subset_sum_reachable(items, target) == _brute(items, target)


class TestEdges:
    def test_empty_reaches_only_zero(self):
        assert subset_sum_reachable([], 0) is True
        assert subset_sum_reachable([], 5) is False


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            subset_sum_reachable(None, 3)

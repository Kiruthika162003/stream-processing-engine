from __future__ import annotations

import itertools
import random

import pytest

from rill.errors import Invalid
from rill.partitionsum import can_partition, closest_partition


def _brute_closest(values: list[int]) -> int:
    best = sum(values)
    for size in range(len(values) + 1):
        for combo in itertools.combinations(range(len(values)), size):
            subset = sum(values[i] for i in combo)
            best = min(best, abs(sum(values) - 2 * subset))
    return best


class TestPerfectSplit:
    def test_an_even_split_exists(self):
        assert can_partition([1, 5, 11, 5])

    def test_an_odd_total_cannot_split_evenly(self):
        assert not can_partition([1, 2, 3, 5])

    def test_a_balanceable_set_has_zero_difference(self):
        assert closest_partition([3, 1, 1, 2, 2, 1]) == 0


class TestClosest:
    def test_an_unbalanceable_set_reports_the_gap(self):
        assert closest_partition([10, 1]) == 9

    def test_it_matches_brute_force(self):
        rng = random.Random(5)
        for _ in range(300):
            values = [rng.randint(0, 15) for _ in range(rng.randint(0, 8))]
            assert closest_partition(values) == _brute_closest(values)

    def test_no_items_has_no_gap(self):
        assert closest_partition([]) == 0


class TestRefusals:
    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            can_partition([1, -2, 3])

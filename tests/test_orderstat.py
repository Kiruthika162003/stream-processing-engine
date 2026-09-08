from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.orderstat import OrderStatistics


class TestConcrete:
    def test_rank_counts_values_at_most_x(self):
        stats = OrderStatistics(max_value=100)
        for value in (10, 20, 20, 40):
            stats.insert(value)
        assert stats.rank(20) == 3  # 10, 20, 20
        assert stats.rank(5) == 0
        assert stats.rank(100) == 4

    def test_select_returns_the_kth_smallest(self):
        stats = OrderStatistics(max_value=100)
        for value in (30, 10, 20, 40):
            stats.insert(value)
        assert stats.select(1) == 10
        assert stats.select(2) == 20
        assert stats.select(4) == 40


class TestAgainstSorted:
    def test_rank_and_select_match_a_sorted_reference(self):
        rng = random.Random(4)
        for _ in range(200):
            stats = OrderStatistics(max_value=100)
            values: list[int] = []
            for _ in range(rng.randint(1, 50)):
                value = rng.randint(1, 100)
                stats.insert(value)
                values.append(value)
            ordered = sorted(values)
            for probe in (1, 50, 100):
                assert stats.rank(probe) == sum(1 for v in values if v <= probe)
            for k in range(1, len(ordered) + 1):
                assert stats.select(k) == ordered[k - 1]


class TestRefusals:
    def test_a_value_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            OrderStatistics(max_value=10).insert(11)

    def test_a_k_out_of_range_is_refused(self):
        stats = OrderStatistics(max_value=10)
        stats.insert(5)
        with pytest.raises(Invalid):
            stats.select(2)

    def test_a_nonpositive_max_value_is_refused(self):
        with pytest.raises(Invalid):
            OrderStatistics(max_value=0)

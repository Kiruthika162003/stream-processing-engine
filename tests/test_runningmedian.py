from __future__ import annotations

import random
import statistics

import pytest

from rill.errors import Invalid
from rill.runningmedian import RunningMedian


class TestCorrectness:
    def test_it_matches_a_full_sort_at_every_step(self):
        rng = random.Random(5)
        for _ in range(300):
            median = RunningMedian()
            seen: list[int] = []
            for _ in range(rng.randint(1, 30)):
                value = rng.randint(0, 100)
                median.add(value)
                seen.append(value)
                assert median.median() == statistics.median(seen)

    def test_an_even_count_averages_the_two_middles(self):
        median = RunningMedian()
        for value in (5, 2, 8, 1):
            median.add(value)
        assert median.median() == 3.5

    def test_an_odd_count_is_the_middle(self):
        median = RunningMedian()
        for value in (5, 2, 8):
            median.add(value)
        assert median.median() == 5.0

    def test_a_single_value_is_its_own_median(self):
        median = RunningMedian()
        median.add(7)
        assert median.median() == 7.0


class TestRefusals:
    def test_the_median_before_any_value_is_refused(self):
        with pytest.raises(Invalid):
            RunningMedian().median()

from __future__ import annotations

import random
import statistics

import pytest

from rill.errors import Invalid
from rill.frugal import FrugalMedian


def _tail_mean(low: int, high: int, seed: int) -> float:
    rng = random.Random(seed)
    frugal = FrugalMedian(step=1)
    frugal.update((low + high) // 2)
    tail = []
    for step in range(10000):
        frugal.update(rng.randint(low, high))
        if step >= 5000:
            tail.append(frugal.median())
    return statistics.fmean(tail)


class TestConvergence:
    def test_it_hovers_around_the_median_of_a_uniform_stream(self):
        # true median of uniform[0, 100] is 50
        assert 45 <= _tail_mean(0, 100, seed=3) <= 55

    def test_it_tracks_a_shifted_distribution(self):
        # true median of uniform[150, 250] is 200
        assert 195 <= _tail_mean(150, 250, seed=5) <= 205


class TestMechanics:
    def test_the_first_sample_seeds_the_estimate(self):
        frugal = FrugalMedian()
        frugal.update(42)
        assert frugal.median() == 42

    def test_a_higher_sample_nudges_up_and_a_lower_one_down(self):
        frugal = FrugalMedian(step=2)
        frugal.update(50)
        frugal.update(90)
        assert frugal.median() == 52
        frugal.update(10)
        assert frugal.median() == 50


class TestRefusals:
    def test_a_nonpositive_step_is_refused(self):
        with pytest.raises(Invalid):
            FrugalMedian(step=0)

    def test_the_median_before_any_sample_is_refused(self):
        with pytest.raises(Invalid):
            FrugalMedian().median()

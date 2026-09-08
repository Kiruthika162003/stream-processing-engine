from __future__ import annotations

import random
import statistics

import pytest

from rill.errors import Invalid
from rill.morris import MorrisCounter


class TestUnbiased:
    def test_the_mean_estimate_tracks_the_true_count(self):
        rng = random.Random(7)
        estimates = []
        exponents = []
        for _ in range(2000):
            counter = MorrisCounter()
            for _ in range(1000):
                counter.increment(rng.random)
            estimates.append(counter.estimate())
            exponents.append(counter.exponent())
        mean = statistics.fmean(estimates)
        assert 900 < mean < 1100  # unbiased around the true 1000
        # the exponent stays near log2(1000), a handful of bits
        assert statistics.median(exponents) <= 12


class TestMechanics:
    def test_the_estimate_is_two_to_the_exponent_minus_one(self):
        counter = MorrisCounter()
        # force three increments with a roll that always fires
        for _ in range(3):
            counter.increment(lambda: 0.0)
        assert counter.exponent() == 3
        assert counter.estimate() == 7

    def test_a_high_roll_never_increments(self):
        counter = MorrisCounter()
        counter.increment(lambda: 0.999)  # above 2^0 = 1? no, 0.999 < 1 fires
        counter.increment(lambda: 0.999)  # now 2^-1 = 0.5, 0.999 > 0.5, no fire
        assert counter.exponent() == 1


class TestRefusals:
    def test_a_roll_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            MorrisCounter().increment(lambda: 1.5)

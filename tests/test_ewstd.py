from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.ewstd import EwStdDev


class TestAdaptiveBand:
    def test_a_small_excursion_stands_out_after_a_calm_stretch(self):
        detector = EwStdDev(alpha=0.2)
        for _ in range(30):
            detector.update(100)
        assert detector.stddev() < 0.01
        assert detector.is_anomaly(110)

    def test_the_same_excursion_is_ordinary_after_a_volatile_stretch(self):
        detector = EwStdDev(alpha=0.2)
        rng = random.Random(1)
        for _ in range(50):
            detector.update(100 + rng.randint(-50, 50))
        assert detector.stddev() > 10
        assert not detector.is_anomaly(110)


class TestTracking:
    def test_the_mean_follows_the_stream(self):
        detector = EwStdDev(alpha=0.5)
        detector.update(0)
        for _ in range(20):
            detector.update(100)
        assert detector.mean() == pytest.approx(100, abs=1)


class TestRefusals:
    def test_an_alpha_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            EwStdDev(alpha=0)

    def test_the_mean_before_any_sample_is_refused(self):
        with pytest.raises(Invalid):
            EwStdDev(alpha=0.5).mean()

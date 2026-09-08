from __future__ import annotations

import random

import pytest

from rill.cusum import Cusum
from rill.errors import Invalid


class TestSmallShift:
    def test_it_catches_a_sustained_shift_within_the_noise(self):
        rng = random.Random(4)
        detector = Cusum(target=0, slack=0.5, threshold=5)
        alarm_at = None
        false_alarm = False
        for step in range(200):
            mean = 0 if step < 100 else 1.0
            reading = detector.update(mean + rng.gauss(0, 1))
            if reading == "up" and alarm_at is None:
                alarm_at = step
            if reading is not None and step < 100:
                false_alarm = True
        assert not false_alarm
        assert alarm_at is not None
        assert 100 <= alarm_at <= 120

    def test_a_downward_shift_alarms_down(self):
        detector = Cusum(target=0, slack=0.5, threshold=3)
        alarm = None
        for _ in range(50):
            alarm = detector.update(-2.0) or alarm
        assert alarm == "down"


class TestReset:
    def test_reset_clears_the_sums(self):
        detector = Cusum(target=0, slack=0.5, threshold=3)
        for _ in range(10):
            detector.update(5.0)
        detector.reset()
        assert detector.update(0.0) is None


class TestRefusals:
    def test_a_nonpositive_threshold_is_refused(self):
        with pytest.raises(Invalid):
            Cusum(target=0, slack=0.5, threshold=0)

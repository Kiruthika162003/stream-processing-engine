from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.watermarkstall import StallDetector


class TestTheDistinction:
    def test_an_advancing_watermark_is_healthy(self):
        detector = StallDetector(stall_threshold=10)
        detector.observe(0, 100, events_in=5)
        detector.observe(20, 120, events_in=5)
        assert detector.verdict().startswith(
            "healthy: watermark advanced 20"
        )

    def test_a_frozen_watermark_with_no_input_is_slow(self):
        detector = StallDetector(stall_threshold=10)
        detector.observe(0, 100, events_in=0)
        detector.observe(20, 100, events_in=0)
        verdict = detector.verdict()
        assert "slow, not stalled" in verdict
        assert "this is not the failure to alarm on" in verdict

    def test_a_frozen_watermark_with_input_is_the_stall(self):
        detector = StallDetector(stall_threshold=10)
        detector.observe(0, 100, events_in=50)
        detector.observe(30, 100, events_in=50)
        verdict = detector.verdict()
        assert verdict.startswith("STALLED: watermark frozen")
        assert "it is time that has died" in verdict
        assert "idle source holding the minimum" in verdict

    def test_early_calls_are_withheld(self):
        detector = StallDetector(stall_threshold=100)
        detector.observe(0, 100, events_in=50)
        detector.observe(5, 100, events_in=50)
        assert detector.verdict() == "too soon to call a stall"


class TestRefusals:
    def test_a_lone_observation_cannot_stall(self):
        detector = StallDetector(stall_threshold=10)
        detector.observe(0, 100, events_in=5)
        with pytest.raises(Invalid):
            detector.verdict()

    def test_negative_thresholds_and_counts_are_refused(self):
        with pytest.raises(Invalid):
            StallDetector(stall_threshold=0)
        with pytest.raises(Invalid):
            StallDetector(stall_threshold=10).observe(0, 5, -1)

from __future__ import annotations

import pytest

from rill.clockdrift import DriftDetector
from rill.errors import Invalid


def detector() -> DriftDetector:
    built = DriftDetector()
    built.sync("fast-box", source_stamp=103, reference_stamp=100)
    built.sync("slow-box", source_stamp=98, reference_stamp=100)
    built.sync("on-time", source_stamp=100, reference_stamp=100)
    return built


class TestDetection:
    def test_the_fast_clock_is_time_travel_not_disorder(self):
        built = DriftDetector()
        verdict = built.sync(
            "fast", source_stamp=105, reference_stamp=100
        )
        assert "runs 5 tick(s) fast" in verdict
        assert "time-traveling, not out of order" in verdict

    def test_the_on_time_clock_says_so(self):
        assert "on-time is on time" in detector().sync(
            "on-time", 100, 100
        )


class TestCorrection:
    def test_the_correction_is_applied_and_raw_kept(self):
        built = detector()
        corrected, story = built.correct("fast-box", 203)
        assert corrected == 200
        assert "raw kept" in story
        assert built.corrections == [
            "fast-box: raw 203 -> 200"
        ]

    def test_the_slow_clock_corrects_upward(self):
        built = detector()
        corrected, _ = built.correct("slow-box", 198)
        assert corrected == 200

    def test_correcting_an_unsynced_clock_is_guessing(self):
        with pytest.raises(Invalid) as caught:
            DriftDetector().correct("mystery", 100)
        assert "correcting an unmeasured clock is guessing" in (
            str(caught.value)
        )


class TestTheReport:
    def test_the_report_names_the_worst_drift(self):
        report = detector().drift_report()
        assert "worst drift fast-box at 3 tick(s)" in report
        assert "diagnosis without treatment" in report

    def test_an_unsynced_detector_is_refused(self):
        with pytest.raises(Invalid):
            DriftDetector().drift_report()

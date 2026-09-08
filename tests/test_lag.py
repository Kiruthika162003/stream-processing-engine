from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.lag import LagTracker


class TestTheNumber:
    def test_lag_moves_with_the_two_rates(self):
        tracker = LagTracker(lag=10)
        assert tracker.observe_window(arrived=5, drained=8) == (
            "lag 7 after +5/-8"
        )

    def test_lag_never_reads_the_future(self):
        tracker = LagTracker(lag=2)
        tracker.observe_window(arrived=0, drained=50)
        assert tracker.lag == 0
        with pytest.raises(Invalid):
            LagTracker(lag=-1)


class TestTheVerdict:
    def test_caught_up_and_holding_is_the_good_sentence(self):
        tracker = LagTracker(lag=0)
        tracker.observe_window(arrived=10, drained=10)
        assert tracker.verdict() == (
            "caught up and holding; the stream is a stream"
        )

    def test_catching_up_states_the_date_in_windows(self):
        tracker = LagTracker(lag=100)
        for _ in range(3):
            tracker.observe_window(arrived=10, drained=30)
        verdict = tracker.verdict()
        assert "lag 40" in verdict
        assert "surplus 20 per window" in verdict
        assert "caught up in 2 window(s)" in verdict

    def test_falling_behind_refuses_to_soften(self):
        tracker = LagTracker(lag=50)
        for _ in range(3):
            tracker.observe_window(arrived=30, drained=10)
        verdict = tracker.verdict()
        assert verdict.startswith("FALLING BEHIND")
        assert "never at these rates" in verdict

    def test_no_windows_makes_lag_a_rumor(self):
        with pytest.raises(Invalid):
            LagTracker(lag=5).verdict()


class TestTheAccusation:
    def test_four_windows_of_growth_name_the_batch_job(self):
        tracker = LagTracker(lag=0)
        for _ in range(4):
            tracker.observe_window(arrived=20, drained=10)
        assert "has not admitted it yet" in (
            tracker.batch_job_check()
        )

    def test_a_recovering_stream_is_not_accused(self):
        tracker = LagTracker(lag=0)
        for _ in range(3):
            tracker.observe_window(arrived=20, drained=10)
        tracker.observe_window(arrived=10, drained=20)
        assert tracker.batch_job_check() == (
            "still a stream, some weeks barely"
        )

    def test_early_accusations_are_withheld(self):
        tracker = LagTracker(lag=0)
        tracker.observe_window(arrived=9, drained=1)
        assert "too soon" in tracker.batch_job_check()

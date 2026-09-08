from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.ratebreaker import RateBreaker


class TestIntermittent:
    def test_a_fifty_percent_failure_rate_trips_without_a_streak(self):
        breaker = RateBreaker(window=10, threshold=0.4, min_samples=10)
        for tick in range(10):
            breaker.record(success=tick % 2 == 0)  # alternating, no run
        assert breaker.failure_rate() == 0.5
        assert breaker.tripped()

    def test_a_healthy_rate_stays_closed(self):
        breaker = RateBreaker(window=10, threshold=0.4, min_samples=10)
        for tick in range(10):
            breaker.record(success=tick != 0)  # one failure in ten
        assert not breaker.tripped()


class TestGuards:
    def test_it_waits_for_the_minimum_samples(self):
        breaker = RateBreaker(window=10, threshold=0.4, min_samples=5)
        breaker.record(success=False)  # 100% failure but only one sample
        assert not breaker.tripped()

    def test_the_window_slides_and_forgets_old_outcomes(self):
        breaker = RateBreaker(window=4, threshold=0.4, min_samples=4)
        for _ in range(4):
            breaker.record(success=False)  # window full of failures
        assert breaker.tripped()
        for _ in range(4):
            breaker.record(success=True)  # push the failures out
        assert not breaker.tripped()


class TestRefusals:
    def test_a_nonpositive_window_is_refused(self):
        with pytest.raises(Invalid):
            RateBreaker(window=0, threshold=0.5)

    def test_a_threshold_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            RateBreaker(window=10, threshold=1.5)

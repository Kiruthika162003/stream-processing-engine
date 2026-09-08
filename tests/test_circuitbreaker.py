from __future__ import annotations

import pytest

from rill.circuitbreaker import CLOSED, HALF_OPEN, OPEN, CircuitBreaker
from rill.errors import Invalid


class TestTripping:
    def test_the_circuit_stays_closed_below_the_threshold(self):
        breaker = CircuitBreaker(threshold=3, cooldown=10)
        breaker.on_failure(now=0)
        breaker.on_failure(now=1)
        assert breaker.state(now=1) == CLOSED
        assert breaker.allow(now=1)

    def test_crossing_the_threshold_trips_open(self):
        breaker = CircuitBreaker(threshold=3, cooldown=10)
        for tick in range(3):
            breaker.on_failure(now=tick)
        assert breaker.state(now=3) == OPEN
        assert not breaker.allow(now=3)

    def test_a_success_resets_the_failure_count(self):
        breaker = CircuitBreaker(threshold=3, cooldown=10)
        breaker.on_failure(now=0)
        breaker.on_failure(now=1)
        breaker.on_success(now=2)
        breaker.on_failure(now=3)
        assert breaker.state(now=3) == CLOSED


class TestHalfOpenRecovery:
    def test_the_cooldown_moves_open_to_half_open(self):
        breaker = CircuitBreaker(threshold=1, cooldown=10)
        breaker.on_failure(now=0)
        assert breaker.state(now=5) == OPEN
        assert breaker.state(now=10) == HALF_OPEN
        assert breaker.allow(now=10)

    def test_a_failed_probe_reopens_for_another_cooldown(self):
        breaker = CircuitBreaker(threshold=1, cooldown=10)
        breaker.on_failure(now=0)
        assert breaker.state(now=10) == HALF_OPEN
        breaker.on_failure(now=10)
        assert breaker.state(now=10) == OPEN
        assert breaker.state(now=20) == HALF_OPEN

    def test_a_successful_probe_closes_the_circuit(self):
        breaker = CircuitBreaker(threshold=1, cooldown=10)
        breaker.on_failure(now=0)
        assert breaker.state(now=10) == HALF_OPEN
        breaker.on_success(now=10)
        assert breaker.state(now=10) == CLOSED


class TestRefusals:
    def test_a_nonpositive_setting_is_refused(self):
        with pytest.raises(Invalid):
            CircuitBreaker(threshold=0, cooldown=1)

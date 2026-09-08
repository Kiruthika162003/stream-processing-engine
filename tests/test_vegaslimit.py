from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.vegaslimit import VegasLimiter


class TestSettling:
    def test_it_settles_near_the_hidden_capacity_without_overshoot(self):
        base, capacity = 10.0, 20
        limiter = VegasLimiter(limit=4, low=2, high=4)
        history = []
        for _ in range(200):
            limit = limiter.limit
            rtt = base * (1 + max(0, limit - capacity) / capacity)
            limiter.observe(rtt)
            history.append(limiter.limit)
        # settles just above capacity, in the small-queue band
        assert 20 <= limiter.limit <= 25
        # steady state, not a sawtooth
        assert max(history[-20:]) - min(history[-20:]) <= 1


class TestGradient:
    def test_no_queue_probes_the_limit_up(self):
        limiter = VegasLimiter(limit=4, low=2, high=4)
        # first sample sets min_rtt and, with no queue, probes up
        assert limiter.observe(10) == 5

    def test_high_queue_backs_the_limit_down(self):
        limiter = VegasLimiter(limit=10, low=2, high=4)
        limiter.observe(10)  # sets min_rtt, probes up to 11
        before = limiter.limit
        result = limiter.observe(100)  # a big queue backs it down
        assert result < before

    def test_estimated_queue_grows_with_latency(self):
        limiter = VegasLimiter(limit=10)
        limiter.observe(10)
        assert limiter.estimated_queue(20) > limiter.estimated_queue(11)


class TestRefusals:
    def test_a_nonpositive_rtt_is_refused(self):
        with pytest.raises(Invalid):
            VegasLimiter().observe(0)

    def test_a_bad_threshold_pair_is_refused(self):
        with pytest.raises(Invalid):
            VegasLimiter(low=5, high=2)

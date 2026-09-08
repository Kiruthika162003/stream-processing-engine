from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.throttle import TokenBucket


def bucket() -> TokenBucket:
    return TokenBucket(refill_per_tick=1, burst=5)


class TestTheBucket:
    def test_a_quiet_key_bursts_its_full_bucket(self):
        limiter = bucket()
        for _ in range(5):
            admitted, _ = limiter.admit("quiet", now=10)
            assert admitted
        admitted, note = limiter.admit("quiet", now=10)
        assert not admitted
        assert "next token in 1 tick(s)" in note

    def test_the_loud_key_settles_to_the_refill_rate(self):
        limiter = bucket()
        admitted_count = 0
        for now in range(10, 20):
            for _ in range(3):
                admitted, _ = limiter.admit("loud", now)
                if admitted:
                    admitted_count += 1
        assert admitted_count == 5 + 9

    def test_the_refusal_teaches_patience_not_hammering(self):
        limiter = bucket()
        for _ in range(5):
            limiter.admit("k", now=0)
        _, note = limiter.admit("k", now=0)
        assert "teaches clients to hammer" in note

    def test_the_bucket_never_overfills(self):
        limiter = bucket()
        limiter.admit("k", now=0)
        limiter.admit("k", now=100)
        assert limiter.tokens["k"] == 4

    def test_wild_configurations_are_refused(self):
        with pytest.raises(Invalid):
            TokenBucket(refill_per_tick=0, burst=5)
        with pytest.raises(Invalid) as caught:
            TokenBucket(refill_per_tick=10, burst=5)
        assert "smaller bucket than the tap" in str(caught.value)


class TestFairness:
    def test_the_hog_is_a_line_item(self):
        limiter = TokenBucket(refill_per_tick=5, burst=50)
        for now in range(10):
            for _ in range(4):
                limiter.admit("hog", now=now)
            limiter.admit("mouse", now=now)
        meter = limiter.fairness_meter()
        assert "hog holds" in meter
        assert "before the other tenants' latency" in meter

    def test_an_unspent_meter_is_refused(self):
        with pytest.raises(Invalid):
            bucket().fairness_meter()

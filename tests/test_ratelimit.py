from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.ratelimit import TokenBucket


class TestTheBucket:
    def test_a_brief_burst_draws_down_and_is_admitted(self):
        bucket = TokenBucket(capacity=10, refill_per_tick=1)
        admitted = sum(
            1
            for _ in range(10)
            if "admitted" in bucket.admit(now=0)
        )
        assert admitted == 10

    def test_a_sustained_overload_runs_dry_and_throttles(self):
        bucket = TokenBucket(capacity=5, refill_per_tick=1)
        for _ in range(5):
            bucket.admit(now=0)
        verdict = bucket.admit(now=0)
        assert "throttled: bucket dry" in verdict

    def test_tokens_refill_over_time(self):
        bucket = TokenBucket(capacity=5, refill_per_tick=1)
        for _ in range(5):
            bucket.admit(now=0)
        verdict = bucket.admit(now=3)
        assert "admitted" in verdict

    def test_a_zero_capacity_bucket_is_refused(self):
        with pytest.raises(Invalid):
            TokenBucket(capacity=0, refill_per_tick=1)


class TestSizing:
    def test_an_oversized_bucket_reports_unused_headroom(self):
        bucket = TokenBucket(capacity=100, refill_per_tick=10)
        bucket.admit(now=0)
        report = bucket.headroom_report()
        assert "oversized: the burst headroom went unused" in (
            report
        )

    def test_an_undersized_bucket_reports_dry_runs(self):
        bucket = TokenBucket(capacity=3, refill_per_tick=1)
        for _ in range(10):
            bucket.admit(now=0)
        report = bucket.headroom_report()
        assert "undersized: the bucket ran dry" in report

    def test_nothing_offered_has_no_report(self):
        with pytest.raises(Invalid):
            TokenBucket(
                capacity=5, refill_per_tick=1
            ).headroom_report()

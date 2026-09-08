from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.leakybucket import LeakyBucket


class TestSmoothing:
    def test_a_burst_leaks_at_the_fixed_rate(self):
        bucket = LeakyBucket(rate=2, capacity=10)
        assert bucket.arrive(10) == 0
        emitted = [bucket.leak() for _ in range(5)]
        assert emitted == [2, 2, 2, 2, 2]
        assert bucket.queued() == 0

    def test_the_burst_spreads_across_the_ticks_the_rate_requires(self):
        bucket = LeakyBucket(rate=2, capacity=10)
        bucket.arrive(10)
        assert bucket.drain_ticks() == 5

    def test_output_never_exceeds_the_rate(self):
        bucket = LeakyBucket(rate=3, capacity=100)
        bucket.arrive(100)
        assert bucket.leak() == 3


class TestOverflow:
    def test_arrivals_past_the_capacity_are_dropped(self):
        bucket = LeakyBucket(rate=2, capacity=5)
        assert bucket.arrive(8) == 3
        assert bucket.queued() == 5

    def test_room_opens_as_the_bucket_leaks(self):
        bucket = LeakyBucket(rate=2, capacity=5)
        bucket.arrive(5)
        bucket.leak()
        assert bucket.arrive(2) == 0
        assert bucket.queued() == 5


class TestRefusals:
    def test_a_nonpositive_rate_is_refused(self):
        with pytest.raises(Invalid):
            LeakyBucket(rate=0, capacity=5)

    def test_a_negative_arrival_is_refused(self):
        with pytest.raises(Invalid):
            LeakyBucket(rate=2, capacity=5).arrive(-1)

from __future__ import annotations

import pytest

from rill.cardinality import LinearCounter
from rill.errors import Invalid


class TestTheEstimate:
    def test_one_hundred_distinct_reads_ninety_nine(self):
        counter = LinearCounter(buckets=256)
        for number in range(100):
            counter.offer(f"user-{number}")
        assert counter.estimate() == 99

    def test_duplicates_do_not_move_the_needle(self):
        counter = LinearCounter(buckets=256)
        for number in range(100):
            counter.offer(f"user-{number}")
            counter.offer(f"user-{number}")
        assert counter.estimate() == 99
        assert counter.offered == 200

    def test_the_degrading_envelope_underestimates(self):
        counter = LinearCounter(buckets=256)
        for number in range(500):
            counter.offer(f"user-{number}")
        assert counter.estimate() == 475
        assert "degrading toward many" in counter.envelope()

    def test_the_comfortable_envelope_says_so(self):
        counter = LinearCounter(buckets=256)
        for number in range(100):
            counter.offer(f"user-{number}")
        envelope = counter.envelope()
        assert envelope.startswith("32% full, comfortable")


class TestTheLimits:
    def test_saturation_refuses_to_pretend(self):
        counter = LinearCounter(buckets=16)
        for number in range(400):
            counter.offer(f"user-{number}")
        with pytest.raises(Invalid) as caught:
            counter.estimate()
        assert "the difference is the entire product" in str(
            caught.value
        )
        assert counter.envelope().startswith("saturated")

    def test_mood_rings_are_refused(self):
        with pytest.raises(Invalid):
            LinearCounter(buckets=8)

    def test_identityless_offers_are_refused(self):
        with pytest.raises(Invalid):
            LinearCounter(buckets=64).offer("")

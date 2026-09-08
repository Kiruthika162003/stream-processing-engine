from __future__ import annotations

import pytest

from rill.bloomdedupe import BloomDeduper
from rill.errors import Invalid


class TestTheGuarantee:
    def test_a_replay_is_never_admitted_as_new(self):
        deduper = BloomDeduper(max_false_positive=0.2)
        admitted = [
            f"evt-{n}"
            for n in range(50)
            if deduper.offer(f"evt-{n}")
        ]
        for item in admitted:
            assert deduper.offer(item) is False

    def test_some_new_events_may_be_dropped_as_collisions(self):
        deduper = BloomDeduper(max_false_positive=0.5)
        admitted = sum(
            1 for n in range(100) if deduper.offer(f"e-{n}")
        )
        assert admitted <= 100

    def test_the_guarantee_states_its_direction(self):
        deduper = BloomDeduper(max_false_positive=0.5)
        deduper.offer("a")
        guarantee = deduper.guarantee()
        assert "never drops a genuinely new event" in guarantee
        assert "may drop a colliding one" in guarantee
        assert "a false drop beats a false pass" in guarantee

    def test_a_nonsense_tolerance_is_refused(self):
        with pytest.raises(Invalid):
            BloomDeduper(max_false_positive=1.5)


class TestTheFillRefusal:
    def test_the_filter_refuses_to_fill_past_tolerance(self):
        deduper = BloomDeduper(max_false_positive=0.05)
        with pytest.raises(Invalid) as caught:
            for number in range(1000):
                deduper.offer(f"flood-{number}")
        assert "climbs invisibly toward useless" in str(
            caught.value
        )

    def test_the_rate_rises_with_insertions(self):
        deduper = BloomDeduper(max_false_positive=0.9)
        before = deduper.false_positive_rate()
        for number in range(50):
            deduper.offer(f"item-{number}")
        assert deduper.false_positive_rate() > before

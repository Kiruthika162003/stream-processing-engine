from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.events import Event
from rill.joins import IntervalJoin


def at(key: str, event_time: int) -> Event:
    return Event(
        key=key, value=1, event_time=event_time,
        arrival=event_time,
    )


class TestMatching:
    def test_the_pair_inside_tolerance_joins(self):
        join = IntervalJoin(tolerance=5)
        join.feed_left(at("order-1", 10))
        notes = join.feed_right(at("order-1", 13))
        assert notes == [
            "order-1: left@10 joins right@13"
        ]

    def test_keys_never_cross(self):
        join = IntervalJoin(tolerance=5)
        join.feed_left(at("order-1", 10))
        assert join.feed_right(at("order-2", 10)) == []

    def test_the_gap_beyond_tolerance_misses(self):
        join = IntervalJoin(tolerance=2)
        join.feed_left(at("order-1", 10))
        assert join.feed_right(at("order-1", 13)) == []

    def test_one_event_can_match_several_partners(self):
        join = IntervalJoin(tolerance=5)
        join.feed_left(at("k", 10))
        join.feed_left(at("k", 12))
        notes = join.feed_right(at("k", 11))
        assert len(notes) == 2

    def test_a_negative_tolerance_matches_nothing(self):
        with pytest.raises(Invalid):
            IntervalJoin(tolerance=-1)


class TestTheUnmatchedExits:
    def test_the_lonely_order_leaves_by_the_named_exit(self):
        join = IntervalJoin(tolerance=3)
        join.feed_left(at("order-9", 10))
        join.feed_right(at("other", 11))
        verdict = join.evict(watermark=20)
        assert "evicted 1 left and 1 right" in verdict
        assert join.unmatched_left == ["order-9@10"]
        assert join.unmatched_right == ["other@11"]

    def test_the_matched_pair_does_not_leak_out_the_exit(self):
        join = IntervalJoin(tolerance=3)
        join.feed_left(at("order-1", 10))
        join.feed_right(at("order-1", 12))
        join.evict(watermark=30)
        assert join.unmatched_left == []
        assert join.unmatched_right == []

    def test_recent_events_stay_buffered(self):
        join = IntervalJoin(tolerance=3)
        join.feed_left(at("order-1", 18))
        join.evict(watermark=20)
        assert join.left_buffer["order-1"]


class TestTheLedger:
    def test_the_ledger_admits_the_losses(self):
        join = IntervalJoin(tolerance=3)
        join.feed_left(at("order-1", 10))
        join.feed_right(at("order-1", 12))
        join.feed_left(at("order-9", 11))
        join.evict(watermark=25)
        ledger = join.ledger()
        assert ledger.startswith(
            "1 match(es), 1 unmatched left, 0 unmatched right, "
            "0 event(s) still buffered"
        )
        assert "hiding its losses" in ledger

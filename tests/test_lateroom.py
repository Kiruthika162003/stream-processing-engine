from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.events import Event
from rill.lateroom import LateRoom


def at(key: str, event_time: int) -> Event:
    return Event(
        key=key, value=1, event_time=event_time,
        arrival=event_time + 50,
    )


def busy_room() -> LateRoom:
    room = LateRoom(patience=20, window_size=10)
    room.admit(at("a", 18), watermark=20)
    room.admit(at("b", 17), watermark=20)
    room.admit(at("c", 12), watermark=20)
    room.admit(at("d", 4), watermark=20)
    return room


class TestAdmission:
    def test_stragglers_are_admitted_with_their_lateness(self):
        room = LateRoom(patience=20, window_size=10)
        verdict = room.admit(at("a", 15), watermark=20)
        assert verdict == "a@15 admitted, 5 tick(s) late"

    def test_commuters_are_refused(self):
        room = LateRoom(patience=20, window_size=10)
        with pytest.raises(Invalid) as caught:
            room.admit(at("a", 25), watermark=20)
        assert "stragglers, not commuters" in str(caught.value)


class TestTheHistogram:
    def test_the_histogram_signs_the_decision(self):
        report = busy_room().histogram()
        assert report.startswith(
            "4 straggler(s): 1-3: 2 (50%), 4-10: 1 (25%), "
            "11+: 1 (25%)"
        )
        assert "waiting to be signed" in report

    def test_the_empty_room_admits_both_readings(self):
        room = LateRoom(patience=5, window_size=10)
        assert room.histogram() == (
            "the room is empty; either on time or lying"
        )


class TestTheTwoExits:
    def test_reconcile_names_the_affected_windows(self):
        room = busy_room()
        verdict = room.reconcile()
        assert verdict.startswith(
            "4 straggler(s) handed to the correction job"
        )
        assert "[0, 10), [10, 20)" in verdict
        assert room.held == []

    def test_expiry_counts_what_it_abandons(self):
        room = busy_room()
        verdict = room.expire_impatient(watermark=30)
        assert verdict.startswith(
            "1 abandoned past the patience horizon of 20, "
            "3 still waiting"
        )
        assert room.expired == 1

    def test_an_empty_reconcile_is_refused(self):
        room = LateRoom(patience=5, window_size=10)
        with pytest.raises(Invalid):
            room.reconcile()

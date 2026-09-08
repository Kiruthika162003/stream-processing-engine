from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.events import Event, Tape


def tangled_tape() -> Tape:
    tape = Tape()
    tape.record(Event(key="a", value=1, event_time=10, arrival=12))
    tape.record(Event(key="b", value=2, event_time=14, arrival=15))
    tape.record(Event(key="a", value=3, event_time=11, arrival=16))
    tape.record(Event(key="c", value=4, event_time=20, arrival=21))
    tape.record(Event(key="b", value=5, event_time=13, arrival=30))
    return tape


class TestTheTwoClocks:
    def test_skew_is_the_transit_gap(self):
        event = Event(key="a", value=1, event_time=10, arrival=17)
        assert event.skew() == 7
        assert "skew 7" in event.line()

    def test_negative_time_is_a_bug_wearing_a_timestamp(self):
        with pytest.raises(Invalid):
            Event(key="a", value=1, event_time=-1, arrival=0)

    def test_a_keyless_event_routes_nowhere(self):
        with pytest.raises(Invalid):
            Event(key="", value=1, event_time=0, arrival=0)


class TestTheTape:
    def test_arrival_order_is_the_guaranteed_order(self):
        tape = tangled_tape()
        arrivals = [e.arrival for e in tape.in_arrival_order()]
        assert arrivals == sorted(arrivals)

    def test_a_rewound_arrival_breaks_the_tape(self):
        tape = tangled_tape()
        with pytest.raises(Invalid):
            tape.record(
                Event(key="x", value=9, event_time=5, arrival=3)
            )

    def test_event_time_order_is_a_reconstruction(self):
        times = [
            e.event_time
            for e in tangled_tape().in_event_time_order()
        ]
        assert times == [10, 11, 13, 14, 20]

    def test_disorder_counts_the_adjacent_inversions(self):
        assert tangled_tape().disorder() == 2

    def test_max_skew_finds_the_straggler(self):
        assert tangled_tape().max_skew() == 17

    def test_the_report_carries_all_three_numbers(self):
        report = tangled_tape().report()
        assert report.startswith(
            "5 event(s), disorder 2, max skew 17"
        )
        assert "priced in hindsight" in report

    def test_the_empty_tape_admits_both_readings(self):
        assert Tape().report() == (
            "empty tape; nothing happened, or nothing arrived"
        )
        with pytest.raises(Invalid):
            Tape().max_skew()

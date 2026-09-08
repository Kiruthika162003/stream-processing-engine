from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.events import Event
from rill.watermark import BoundedWatermark


def at(event_time: int, arrival: int = 0) -> Event:
    return Event(
        key="k",
        value=1,
        event_time=event_time,
        arrival=arrival or event_time,
    )


class TestAdvancing:
    def test_the_watermark_trails_by_the_bound(self):
        mark = BoundedWatermark(lateness_bound=5)
        verdict = mark.observe(at(20))
        assert verdict == (
            "watermark advances to 15; events at or before it "
            "are now presumed arrived"
        )

    def test_the_watermark_never_moves_backward(self):
        mark = BoundedWatermark(lateness_bound=5)
        mark.observe(at(20))
        mark.observe(at(17))
        assert mark.current == 15

    def test_a_negative_bound_promises_the_future(self):
        with pytest.raises(Invalid):
            BoundedWatermark(lateness_bound=-1)


class TestLateness:
    def test_behind_the_watermark_is_late_and_says_why(self):
        mark = BoundedWatermark(lateness_bound=2)
        mark.observe(at(20))
        verdict = mark.observe(at(18))
        assert verdict.startswith("k@18 is LATE")
        assert "does not reopen" in verdict
        assert mark.late_events == 1

    def test_inside_the_bound_is_not_late(self):
        mark = BoundedWatermark(lateness_bound=5)
        mark.observe(at(20))
        verdict = mark.observe(at(17))
        assert "observed, watermark holds" in verdict
        assert mark.late_events == 0

    def test_would_be_late_asks_without_recording(self):
        mark = BoundedWatermark(lateness_bound=2)
        mark.observe(at(20))
        assert mark.would_be_late(18)
        assert not mark.would_be_late(19)
        assert mark.late_events == 0


class TestTheLedger:
    def test_the_ledger_carries_the_bet_and_its_evidence(self):
        mark = BoundedWatermark(lateness_bound=2)
        mark.observe(at(20))
        mark.observe(at(10))
        mark.observe(at(25))
        ledger = mark.ledger()
        assert ledger.startswith(
            "watermark 23 after 2 advance(s), bound 2, "
            "1 late event(s)"
        )
        assert "re-size it" in ledger

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.eventtimesort import EventTimeSorter


class TestReordering:
    def test_disordered_arrivals_come_out_in_event_time_order(self):
        sorter = EventTimeSorter()
        for event_time, value in [(5, "e"), (1, "a"), (3, "c"), (2, "b"), (4, "d")]:
            sorter.add(event_time, value)
        assert sorter.advance(3) == [(1, "a"), (2, "b"), (3, "c")]
        assert sorter.advance(5) == [(4, "d"), (5, "e")]

    def test_events_ahead_of_the_watermark_stay_buffered(self):
        sorter = EventTimeSorter()
        sorter.add(10, "future")
        assert sorter.advance(5) == []
        assert sorter.buffered() == 1


class TestLateness:
    def test_an_event_behind_the_watermark_is_dropped(self):
        sorter = EventTimeSorter()
        sorter.advance(5)
        assert not sorter.add(4, "late")
        assert sorter.dropped() == 1


class TestRefusals:
    def test_a_backward_watermark_is_refused(self):
        sorter = EventTimeSorter()
        sorter.advance(10)
        with pytest.raises(Invalid):
            sorter.advance(5)

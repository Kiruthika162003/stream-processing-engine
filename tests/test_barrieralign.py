from __future__ import annotations

import pytest

from rill.barrieralign import BarrierTracker
from rill.errors import Invalid


class TestAligned:
    def test_alignment_delay_is_the_slowest_barriers_lag(self):
        tracker = BarrierTracker(channels=3, mode="aligned")
        tracker.barrier(0, at=100)
        tracker.barrier(1, at=105)
        tracker.barrier(2, at=140)
        assert tracker.aligned()
        assert tracker.alignment_delay() == 40

    def test_an_early_channel_buffers_until_the_last_barrier(self):
        tracker = BarrierTracker(channels=2, mode="aligned")
        tracker.barrier(0, at=100)
        tracker.record_in_flight(0, 30)
        tracker.record_in_flight(0, 20)
        assert tracker.buffered_during_alignment() == 50

    def test_a_channel_still_waited_on_does_not_buffer(self):
        tracker = BarrierTracker(channels=2, mode="aligned")
        tracker.barrier(0, at=100)
        tracker.record_in_flight(1, 40)
        assert tracker.buffered_during_alignment() == 0

    def test_delay_is_refused_until_every_barrier_lands(self):
        tracker = BarrierTracker(channels=2, mode="aligned")
        tracker.barrier(0, at=100)
        with pytest.raises(Invalid):
            tracker.alignment_delay()


class TestUnaligned:
    def test_the_snapshot_starts_on_the_first_barrier(self):
        tracker = BarrierTracker(channels=3, mode="unaligned")
        tracker.barrier(0, at=100)
        tracker.record_in_flight(1, 25)
        tracker.record_in_flight(2, 15)
        assert tracker.absorbed_in_flight() == 40

    def test_nothing_is_absorbed_before_the_first_barrier(self):
        tracker = BarrierTracker(channels=3, mode="unaligned")
        tracker.record_in_flight(1, 25)
        assert tracker.absorbed_in_flight() == 0


class TestRefusals:
    def test_an_unknown_mode_is_refused(self):
        with pytest.raises(Invalid):
            BarrierTracker(channels=2, mode="eventual")

    def test_zero_channels_is_refused(self):
        with pytest.raises(Invalid):
            BarrierTracker(channels=0, mode="aligned")

    def test_an_out_of_range_channel_is_refused(self):
        tracker = BarrierTracker(channels=2, mode="aligned")
        with pytest.raises(Invalid):
            tracker.barrier(5, at=0)

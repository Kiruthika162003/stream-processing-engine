from __future__ import annotations

import pytest

from rill.chandylamport import SnapshotProcess
from rill.errors import Invalid


class TestInFlightCapture:
    def test_a_message_after_the_snapshot_is_recorded_as_channel_state(self):
        proc = SnapshotProcess(channels=("up",))
        proc.snapshot("balance=100")
        assert proc.receive("up", "credit=5") == "recorded in flight"
        assert proc.in_flight("up") == ["credit=5"]

    def test_a_message_after_the_marker_is_processed_not_recorded(self):
        proc = SnapshotProcess(channels=("up",))
        proc.snapshot("balance=100")
        proc.marker("up")
        assert proc.receive("up", "credit=9") == "processed normally"
        assert proc.in_flight("up") == []

    def test_recording_stops_per_channel_at_its_own_marker(self):
        proc = SnapshotProcess(channels=("a", "b"))
        proc.snapshot("s")
        proc.receive("a", "m1")
        proc.marker("a")
        proc.receive("a", "after")
        proc.receive("b", "m2")
        assert proc.in_flight("a") == ["m1"]
        assert proc.in_flight("b") == ["m2"]


class TestCompletion:
    def test_the_snapshot_completes_when_every_channel_closes(self):
        proc = SnapshotProcess(channels=("a", "b"))
        proc.snapshot("s")
        proc.marker("a")
        assert not proc.complete()
        proc.marker("b")
        assert proc.complete()
        assert proc.local_state() == "s"

    def test_a_second_snapshot_call_does_not_overwrite_the_first(self):
        proc = SnapshotProcess(channels=("a",))
        proc.snapshot("first")
        proc.snapshot("second")
        assert proc.local_state() == "first"


class TestRefusals:
    def test_no_channels_is_refused(self):
        with pytest.raises(Invalid):
            SnapshotProcess(channels=())

    def test_a_marker_before_the_snapshot_is_refused(self):
        proc = SnapshotProcess(channels=("a",))
        with pytest.raises(Invalid):
            proc.marker("a")

    def test_state_before_the_snapshot_is_refused(self):
        proc = SnapshotProcess(channels=("a",))
        with pytest.raises(Invalid):
            proc.local_state()

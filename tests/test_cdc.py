from __future__ import annotations

import pytest

from rill.cdc import ChangeCapture
from rill.errors import Invalid


def diary() -> ChangeCapture:
    capture = ChangeCapture()
    capture.record(1, "insert", "user-1", None, "alice")
    capture.record(2, "insert", "user-2", None, "bob")
    capture.record(3, "update", "user-1", "alice", "alice-v2")
    capture.record(4, "delete", "user-2", "bob", None)
    return capture


class TestTheKinds:
    def test_updates_carry_both_images(self):
        capture = ChangeCapture()
        with pytest.raises(Invalid) as caught:
            capture.record(1, "update", "k", None, "new")
        assert "what changed, not just what is" in str(
            caught.value
        )

    def test_a_delete_is_an_event_not_an_absence(self):
        capture = ChangeCapture()
        with pytest.raises(Invalid):
            capture.record(1, "delete", "k", "old", "new")

    def test_commit_order_is_the_only_order(self):
        capture = diary()
        with pytest.raises(Invalid):
            capture.record(2, "insert", "late", None, "x")


class TestSnapshots:
    def test_the_snapshot_replays_the_diary_to_a_position(self):
        assert diary().snapshot_at(3) == {
            "user-1": "alice-v2",
            "user-2": "bob",
        }

    def test_the_delete_removes_from_later_snapshots(self):
        assert diary().snapshot_at(4) == {
            "user-1": "alice-v2"
        }


class TestTheSeam:
    def test_the_clean_seam_holds(self):
        verdict = diary().onboard(
            snapshot_position=2, tail_from=3
        )
        assert verdict.startswith(
            "onboarded clean: snapshot of 2 row(s) at 2, "
            "tail of 2 change(s) from 3"
        )

    def test_the_gap_is_the_first_wound(self):
        verdict = diary().onboard(
            snapshot_position=1, tail_from=4
        )
        assert verdict.startswith("GAP at the seam: 2")
        assert "missing rows" in verdict

    def test_the_overlap_is_the_second_wound(self):
        verdict = diary().onboard(
            snapshot_position=3, tail_from=2
        )
        assert verdict.startswith("OVERLAP at the seam: 2")
        assert "duplicates" in verdict

from __future__ import annotations

import pytest

from rill.checkpoint import BarrierOperator, recovery_drill
from rill.errors import Invalid


def two_input() -> BarrierOperator:
    return BarrierOperator(name="join", inputs=2)


class TestAlignment:
    def test_the_first_barrier_waits_and_buffers_the_eager(self):
        operator = two_input()
        operator.feed(0, 3)
        verdict = operator.barrier(0, barrier_id=1)
        assert "waiting for 1 more, buffering the eager" in verdict
        note = operator.feed(0, 9)
        assert "smear the photograph" in note
        assert operator.state == 3

    def test_alignment_snapshots_then_releases_the_buffer(self):
        operator = two_input()
        operator.feed(0, 3)
        operator.barrier(0, barrier_id=1)
        operator.feed(0, 9)
        operator.feed(1, 4)
        verdict = operator.barrier(1, barrier_id=1)
        assert verdict.startswith(
            "aligned: snapshot 1 = 7, 1 buffered event(s) "
            "released"
        )
        assert operator.state == 16

    def test_a_channel_cannot_deliver_the_barrier_twice(self):
        operator = two_input()
        operator.barrier(0, barrier_id=1)
        with pytest.raises(Invalid):
            operator.barrier(0, barrier_id=1)

    def test_unknown_channels_are_refused(self):
        with pytest.raises(Invalid):
            two_input().feed(5, 1)


class TestRecovery:
    def test_restore_rewinds_to_the_snapshot(self):
        operator = BarrierOperator(name="sum", inputs=1)
        operator.feed(0, 3)
        operator.barrier(0, barrier_id=1)
        operator.feed(0, 100)
        assert operator.restore(1) == (
            "sum restored to snapshot 1 (3)"
        )
        assert operator.state == 3

    def test_a_missing_snapshot_cannot_restore(self):
        with pytest.raises(Invalid):
            two_input().restore(9)

    def test_the_drill_proves_the_one_sentence(self):
        verdict = recovery_drill()
        assert "untroubled ends at 18" in verdict
        assert "identical, the only sentence" in verdict
        assert "DIVERGED" not in verdict

from __future__ import annotations

import pytest

from rill.epochs import EpochSink
from rill.errors import Halted, Invalid


class TestTheTwoStep:
    def test_rows_land_together_or_not_at_all(self):
        sink = EpochSink()
        sink.stage(1, "row-a")
        sink.stage(1, "row-b")
        assert sink.committed_rows == []
        verdict = sink.commit(1)
        assert verdict == (
            "epoch 1 committed atomically: 2 row(s) land "
            "together"
        )

    def test_a_committed_epoch_refuses_new_rows(self):
        sink = EpochSink()
        sink.stage(1, "row-a")
        sink.commit(1)
        with pytest.raises(Halted) as caught:
            sink.stage(1, "row-late")
        assert "would edit history" in str(caught.value)

    def test_an_empty_commit_is_a_misfire(self):
        with pytest.raises(Invalid):
            EpochSink().commit(9)


class TestTheTwoCrashes:
    def test_the_crash_before_commit_discards_and_replays(self):
        sink = EpochSink()
        sink.stage(1, "row-a")
        sink.stage(1, "row-b")
        recovery = sink.crash_recovery()
        assert "discards 2 pending row(s)" in recovery
        sink.stage(1, "row-a")
        sink.stage(1, "row-b")
        sink.commit(1)
        assert "each exactly once" in sink.audit()

    def test_the_crash_after_commit_skips_the_replay(self):
        sink = EpochSink()
        sink.stage(1, "row-a")
        sink.commit(1)
        sink.crash_recovery()
        verdict = sink.commit(1)
        assert "the sink learned to count" in verdict
        audit = sink.audit()
        assert audit.startswith(
            "1 row(s), each exactly once, 1 replay(s) refused"
        )

    def test_a_quiet_crash_costs_nothing(self):
        assert EpochSink().crash_recovery() == (
            "nothing pending; the crash cost nothing"
        )


class TestTheAudit:
    def test_duplicates_would_be_named_as_failure(self):
        sink = EpochSink()
        sink.committed_rows = ["r1", "r1"]
        assert sink.audit().startswith("DUPLICATES: 1 row(s)")

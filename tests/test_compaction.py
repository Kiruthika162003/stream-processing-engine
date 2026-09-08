from __future__ import annotations

import pytest

from rill.compaction import CompactedLog
from rill.errors import Invalid


def busy_log() -> CompactedLog:
    log = CompactedLog(tombstone_grace=50)
    log.append("user-1", "alice-v1", 1)
    log.append("user-2", "bob-v1", 2)
    log.append("user-1", "alice-v2", 3)
    log.append("user-1", "alice-v3", 4)
    log.delete("user-2", 5)
    return log


class TestTheSqueeze:
    def test_only_the_newest_truth_survives(self):
        log = busy_log()
        verdict = log.compact(now_offset=10)
        assert verdict.startswith(
            "5 record(s) squeezed to 2, 1 tombstone(s) still "
            "standing guard"
        )
        assert log.restore() == {"user-1": "alice-v3"}

    def test_offsets_only_grow(self):
        log = busy_log()
        with pytest.raises(Invalid):
            log.append("user-3", "x", 2)

    def test_deletion_is_a_marker_not_an_absence(self):
        log = busy_log()
        verdict = log.delete("user-1", 6)
        assert "gone on purpose is different from never" in (
            verdict
        )


class TestTheTombstone:
    def test_the_guarded_tombstone_deletes_on_restore(self):
        log = busy_log()
        log.compact(now_offset=10)
        restored = log.restore()
        assert "user-2" not in restored
        check = log.resurrection_check(restored, {"user-2"})
        assert "the deleted stay deleted" in check

    def test_the_early_sweep_resurrects_the_dead(self):
        log = busy_log()
        log.compact(now_offset=100)
        state = log.restore()
        stale_reader_state = dict(state)
        stale_reader_state["user-2"] = "bob-v1"
        check = log.resurrection_check(
            stale_reader_state, {"user-2"}
        )
        assert check.startswith("RESURRECTION: user-2")
        assert "before every restorer had seen it" in check

    def test_the_sweep_is_counted(self):
        log = busy_log()
        verdict = log.compact(now_offset=100)
        assert "1 swept past their grace" in verdict

from __future__ import annotations

import pytest

from rill.changelog import Changelog
from rill.errors import Invalid


def worked_log() -> Changelog:
    log = Changelog()
    for sequence in range(1, 101):
        log.record_put(sequence, f"k{sequence % 10}", sequence)
    return log


class TestTheLog:
    def test_replay_rebuilds_the_latest_state(self):
        log = worked_log()
        state, story = log.restore()
        assert state["k0"] == 100
        assert state["k1"] == 91
        assert "full replay of 100 record(s)" in story

    def test_deletes_replay_as_absence(self):
        log = Changelog()
        log.record_put(1, "a", 5)
        log.record_delete(2, "a")
        state, _ = log.restore()
        assert state == {}

    def test_sequences_only_grow(self):
        log = worked_log()
        with pytest.raises(Invalid):
            log.record_put(50, "k", 1)


class TestTheSnapshot:
    def test_the_snapshot_truncates_the_redundant(self):
        log = worked_log()
        verdict = log.snapshot(sequence=100)
        assert verdict == (
            "snapshot at 100: 10 key(s) captured, 100 "
            "changelog record(s) now redundant and truncated"
        )
        assert log.entries == []

    def test_restore_is_bounded_by_the_interval(self):
        log = worked_log()
        log.snapshot(sequence=100)
        for sequence in range(101, 106):
            log.record_put(sequence, "k-new", sequence)
        state, story = log.restore()
        assert state["k0"] == 100
        assert state["k-new"] == 105
        assert (
            "snapshot at 100 plus 5 suffix record(s)"
        ) in story
        assert "not the job's age" in story

    def test_the_two_restores_agree(self):
        with_snapshot = worked_log()
        with_snapshot.snapshot(sequence=100)
        for sequence in range(101, 106):
            with_snapshot.record_put(sequence, "k9", sequence)
        without = worked_log()
        for sequence in range(101, 106):
            without.record_put(sequence, "k9", sequence)
        assert with_snapshot.restore()[0] == (
            without.restore()[0]
        )

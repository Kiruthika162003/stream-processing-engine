from __future__ import annotations

import pytest

from rill.errors import Invalid, Missing
from rill.mvcc import MvccStore


class TestRepeatableRead:
    def test_a_snapshot_sees_the_version_current_at_its_timestamp(self):
        store = MvccStore()
        store.write("k", "v1", commit_ts=10)
        assert store.read("k", snapshot_ts=15) == "v1"

    def test_a_later_write_is_invisible_to_the_earlier_snapshot(self):
        store = MvccStore()
        store.write("k", "v1", commit_ts=10)
        store.write("k", "v2", commit_ts=20)
        assert store.read("k", snapshot_ts=15) == "v1"
        assert store.read("k", snapshot_ts=25) == "v2"

    def test_a_read_before_any_version_is_missing(self):
        store = MvccStore()
        store.write("k", "v1", commit_ts=10)
        with pytest.raises(Missing):
            store.read("k", snapshot_ts=5)


class TestGarbageCollection:
    def test_versions_behind_the_horizon_but_the_newest_are_collectable(self):
        store = MvccStore()
        store.write("k", "v1", commit_ts=10)
        store.write("k", "v2", commit_ts=20)
        store.write("k", "v3", commit_ts=30)
        # horizon 25 covers v1 and v2; v2 is the visible one, v1 is dead
        assert store.collectable(horizon_ts=25) == 1

    def test_a_single_version_is_never_collectable(self):
        store = MvccStore()
        store.write("k", "v1", commit_ts=10)
        assert store.collectable(horizon_ts=100) == 0


class TestRefusals:
    def test_a_non_increasing_commit_is_refused(self):
        store = MvccStore()
        store.write("k", "v1", commit_ts=10)
        with pytest.raises(Invalid):
            store.write("k", "v2", commit_ts=10)

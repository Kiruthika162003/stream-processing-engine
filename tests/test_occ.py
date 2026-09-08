from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.occ import OccStore


class TestUncontended:
    def test_a_commit_on_the_read_version_succeeds(self):
        store = OccStore()
        _, version = store.read()
        assert store.commit(version, "v1")
        assert store.read() == ("v1", 1)


class TestConflict:
    def test_the_second_writer_of_a_pair_is_refused(self):
        store = OccStore()
        _, version_a = store.read()
        _, version_b = store.read()  # both read version 0
        assert store.commit(version_a, "from a")  # a wins
        assert not store.commit(version_b, "from b")  # b's version is stale

    def test_the_loser_succeeds_after_a_fresh_read(self):
        store = OccStore()
        _, version_a = store.read()
        store.commit(version_a, "from a")
        _, fresh = store.read()  # b retries from a fresh read
        assert store.commit(fresh, "from b")
        assert store.read() == ("from b", 2)


class TestRefusals:
    def test_a_negative_version_is_refused(self):
        with pytest.raises(Invalid):
            OccStore().commit(-1, "v")

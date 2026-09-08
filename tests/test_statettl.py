from __future__ import annotations

import pytest

from rill.errors import Invalid, Missing
from rill.statettl import TtlStore


class TestReadHonoursTtl:
    def test_a_fresh_key_reads_back(self):
        store = TtlStore(ttl=10)
        store.write("a", "one", now=0)
        assert store.read("a", now=5) == "one"

    def test_a_stale_key_reads_as_missing(self):
        store = TtlStore(ttl=10)
        store.write("a", "one", now=0)
        with pytest.raises(Missing) as caught:
            store.read("a", now=10)
        assert "expired under the ttl" in str(caught.value)

    def test_an_absent_key_is_missing(self):
        store = TtlStore(ttl=10)
        with pytest.raises(Missing):
            store.read("ghost", now=0)


class TestLazyLeak:
    def test_write_once_keys_are_never_reclaimed_by_reading(self):
        store = TtlStore(ttl=10)
        for number in range(100):
            store.write(f"key-{number}", "v", now=0)
        assert store.footprint() == 100
        with pytest.raises(Missing):
            store.read("key-0", now=100)
        assert store.footprint() == 99

    def test_sweep_reclaims_the_whole_dead_pile_at_once(self):
        store = TtlStore(ttl=10)
        for number in range(100):
            store.write(f"key-{number}", "v", now=0)
        reclaimed = store.sweep(now=100)
        assert reclaimed == 100
        assert store.footprint() == 0

    def test_sweep_spares_the_still_live_keys(self):
        store = TtlStore(ttl=10)
        store.write("old", "v", now=0)
        store.write("new", "v", now=95)
        assert store.sweep(now=100) == 1
        assert store.read("new", now=100) == "v"


class TestRefusals:
    def test_a_nonpositive_ttl_is_refused(self):
        with pytest.raises(Invalid):
            TtlStore(ttl=0)

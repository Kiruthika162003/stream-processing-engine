from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.lru import LruCache


class TestBasics:
    def test_eviction_drops_the_least_recently_used(self):
        cache = LruCache(capacity=2)
        cache.put("a", "1")
        cache.put("b", "2")
        assert cache.put("c", "3") == "a"
        assert cache.keys() == ["b", "c"]

    def test_a_get_promotes_a_key_to_most_recent(self):
        cache = LruCache(capacity=2)
        cache.put("a", "1")
        cache.put("b", "2")
        cache.get("a")  # a is now most recent
        assert cache.put("c", "3") == "b"

    def test_a_miss_returns_none(self):
        cache = LruCache(capacity=2)
        assert cache.get("absent") is None


class TestScanThrash:
    def test_a_scan_larger_than_the_cache_evicts_the_working_set(self):
        cache = LruCache(capacity=3)
        for key in ("a", "b", "c"):
            cache.put(key, "hot")
        for number in range(5):
            cache.put(f"scan-{number}", "once")
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.get("c") is None
        assert cache.hit_rate() == 0.0

    def test_the_scan_leavings_are_what_remain(self):
        cache = LruCache(capacity=3)
        for key in ("a", "b", "c"):
            cache.put(key, "hot")
        for number in range(5):
            cache.put(f"scan-{number}", "once")
        assert cache.keys() == ["scan-2", "scan-3", "scan-4"]


class TestRefusals:
    def test_a_nonpositive_capacity_is_refused(self):
        with pytest.raises(Invalid):
            LruCache(capacity=0)

    def test_hit_rate_before_any_access_is_refused(self):
        with pytest.raises(Invalid):
            LruCache(capacity=2).hit_rate()

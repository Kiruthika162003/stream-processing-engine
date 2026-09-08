from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.tinylfu import TinyLfuCache


class TestScanResistance:
    def test_a_scan_cannot_evict_the_hot_working_set(self):
        cache = TinyLfuCache(capacity=3)
        for _ in range(10):
            for key in ("a", "b", "c"):
                if cache.get(key) is None:
                    cache.put(key, "hot")
        rejected = 0
        for number in range(5):
            if cache.put(f"scan-{number}", "once") == f"scan-{number}":
                rejected += 1
        assert rejected == 5
        assert cache.keys() == ["a", "b", "c"]


class TestAdmission:
    def test_a_newcomer_fills_free_space_without_a_contest(self):
        cache = TinyLfuCache(capacity=2)
        assert cache.put("x", "1") is None
        assert cache.put("y", "2") is None

    def test_a_hotter_newcomer_evicts_a_colder_victim(self):
        cache = TinyLfuCache(capacity=2)
        cache.put("x", "1")
        cache.put("y", "2")
        for _ in range(3):
            cache.get("z")  # z builds frequency while missing
        assert cache.put("z", "3") == "x"
        resident = cache.keys()
        assert "z" in resident


class TestRefusals:
    def test_a_nonpositive_capacity_is_refused(self):
        with pytest.raises(Invalid):
            TinyLfuCache(capacity=0)

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.writecache import WriteBackCache, WriteThroughCache


class TestWriteThrough:
    def test_every_write_hits_the_store(self):
        cache = WriteThroughCache()
        for value in range(5):
            cache.write("A", str(value))
        assert cache.store_writes() == 5


class TestWriteBack:
    def test_repeated_writes_coalesce_to_one_store_write(self):
        cache = WriteBackCache()
        for value in range(5):
            cache.write("A", str(value))
        assert cache.store_writes() == 0  # nothing flushed yet
        assert cache.flush() == 1  # only the latest A is written
        assert cache.store_writes() == 1

    def test_a_read_returns_the_latest_value(self):
        cache = WriteBackCache()
        cache.write("A", "old")
        cache.write("A", "new")
        assert cache.read("A") == "new"


class TestCrashLoss:
    def test_a_crash_loses_the_unflushed_dirty_entries(self):
        cache = WriteBackCache()
        for key in ("A", "B", "C"):
            cache.write(key, "v")
        assert cache.crash() == 3

    def test_flushed_entries_are_not_lost_on_a_later_crash(self):
        cache = WriteBackCache()
        cache.write("A", "v")
        cache.flush()
        cache.write("B", "v")
        assert cache.crash() == 1  # only B was dirty


class TestRefusals:
    def test_reading_an_absent_key_is_refused(self):
        with pytest.raises(Invalid):
            WriteBackCache().read("ghost")

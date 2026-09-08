from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.rollingsink import RollingSink


class TestSizeRoll:
    def test_a_full_file_rolls_on_size(self):
        sink = RollingSink(max_records=3, max_age=1000, idle_timeout=100)
        for _ in range(3):
            sink.write("b", now=0)
        assert sink.open_buckets() == []
        assert sink.committed() == [("b", 3, "size")]


class TestQuietBucketStranded:
    def test_a_quiet_bucket_stays_open_without_the_age_trigger(self):
        sink = RollingSink(max_records=10, max_age=1000, idle_timeout=1000)
        sink.write("quiet", now=0)
        sink.tick(now=50)
        assert sink.open_buckets() == ["quiet"]
        assert sink.committed() == []

    def test_the_idle_trigger_flushes_the_quiet_bucket(self):
        sink = RollingSink(max_records=10, max_age=1000, idle_timeout=30)
        sink.write("quiet", now=0)
        sink.tick(now=30)
        assert sink.open_buckets() == []
        assert sink.committed() == [("quiet", 1, "idle")]

    def test_the_age_trigger_commits_a_file_open_too_long(self):
        sink = RollingSink(max_records=10, max_age=100, idle_timeout=1000)
        sink.write("slow", now=0)
        sink.write("slow", now=90)
        sink.tick(now=100)
        assert sink.committed() == [("slow", 2, "age")]


class TestRefusals:
    def test_a_nonpositive_trigger_is_refused(self):
        with pytest.raises(Invalid):
            RollingSink(max_records=0, max_age=1, idle_timeout=1)

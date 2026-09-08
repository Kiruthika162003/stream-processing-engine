from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.groupcommit import GroupCommitLog


class TestBatchCommit:
    def test_a_full_batch_commits_with_one_fsync(self):
        log = GroupCommitLog(max_batch=3, max_wait=1000)
        assert not log.append("a", now=0)
        assert not log.append("b", now=0)
        assert log.append("c", now=0)  # batch full, commits
        assert log.fsyncs() == 1
        assert log.durable() == 3

    def test_a_partial_batch_waits_pending(self):
        log = GroupCommitLog(max_batch=3, max_wait=1000)
        log.append("a", now=0)
        assert log.pending() == 1
        assert log.fsyncs() == 0


class TestTimedFlush:
    def test_the_timer_flushes_a_partial_batch(self):
        log = GroupCommitLog(max_batch=100, max_wait=50)
        log.append("a", now=0)
        assert not log.tick(now=40)
        assert log.tick(now=50)
        assert log.durable() == 1
        assert log.fsyncs() == 1


class TestAmortization:
    def test_a_thousand_writes_cost_a_fraction_of_the_fsyncs(self):
        log = GroupCommitLog(max_batch=50, max_wait=10_000)
        now = 0
        for number in range(1000):
            log.append(f"r{number}", now=now)
            now += 1
        log.tick(now=now + 10_000)
        assert log.durable() == 1000
        assert log.fsyncs() == 20  # 1000 / 50, not 1000


class TestRefusals:
    def test_a_nonpositive_setting_is_refused(self):
        with pytest.raises(Invalid):
            GroupCommitLog(max_batch=0, max_wait=10)

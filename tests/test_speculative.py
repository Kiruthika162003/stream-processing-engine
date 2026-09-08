from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.speculative import Speculator


class TestWhenToSpeculate:
    def test_a_task_within_slack_gets_no_backup(self):
        spec = Speculator(slack=10)
        assert not spec.should_speculate("t", elapsed=105, typical=100)

    def test_a_task_past_the_slack_earns_a_backup(self):
        spec = Speculator(slack=10)
        assert spec.should_speculate("t", elapsed=120, typical=100)


class TestFencedCommit:
    def test_the_first_copy_to_finish_wins(self):
        spec = Speculator(slack=10)
        spec.start("t", 0)
        spec.start("t", 1)
        assert spec.running_copies("t") == 2
        assert spec.commit("t", 1) is True
        assert spec.winner("t") == 1

    def test_the_losing_copy_commit_is_a_no_op(self):
        spec = Speculator(slack=10)
        spec.start("t", 0)
        spec.start("t", 1)
        spec.commit("t", 1)
        assert spec.commit("t", 0) is False
        assert spec.winner("t") == 1

    def test_committing_an_unstarted_attempt_is_refused(self):
        spec = Speculator(slack=10)
        spec.start("t", 0)
        with pytest.raises(Invalid):
            spec.commit("t", 9)


class TestRefusals:
    def test_a_nonpositive_slack_is_refused(self):
        with pytest.raises(Invalid):
            Speculator(slack=0)

    def test_a_winner_before_any_commit_is_refused(self):
        spec = Speculator(slack=10)
        spec.start("t", 0)
        with pytest.raises(Invalid):
            spec.winner("t")

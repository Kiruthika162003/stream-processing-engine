from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.raftcommit import RaftLeader


class TestPriorTermRule:
    def test_a_prior_term_entry_on_a_majority_is_not_committed(self):
        leader = RaftLeader(servers=3, current_term=2)
        leader.append(1)  # index 1, an entry from term 1
        leader.replicated("f1", 1)  # leader plus f1 is a majority
        assert leader.commit_index() == 0

    def test_a_current_term_entry_commits_the_prior_one_beneath_it(self):
        leader = RaftLeader(servers=3, current_term=2)
        leader.append(1)
        leader.replicated("f1", 1)
        leader.append(2)  # index 2, current term
        leader.replicated("f1", 2)
        assert leader.commit_index() == 2


class TestMajority:
    def test_without_a_majority_nothing_commits(self):
        leader = RaftLeader(servers=5, current_term=1)
        leader.append(1)
        leader.replicated("f1", 1)  # leader + f1 = 2, majority is 3
        assert leader.commit_index() == 0

    def test_a_majority_of_a_current_term_entry_commits_it(self):
        leader = RaftLeader(servers=5, current_term=1)
        leader.append(1)
        leader.replicated("f1", 1)
        leader.replicated("f2", 1)  # leader + two = 3, a majority
        assert leader.commit_index() == 1


class TestRefusals:
    def test_appending_a_future_term_is_refused(self):
        leader = RaftLeader(servers=3, current_term=2)
        with pytest.raises(Invalid):
            leader.append(3)

    def test_replicating_beyond_the_log_is_refused(self):
        leader = RaftLeader(servers=3, current_term=1)
        leader.append(1)
        with pytest.raises(Invalid):
            leader.replicated("f1", 5)

    def test_zero_servers_is_refused(self):
        with pytest.raises(Invalid):
            RaftLeader(servers=0, current_term=1)

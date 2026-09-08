from __future__ import annotations

import pytest

from rill.bully import BullyElection
from rill.errors import Invalid


class TestLeader:
    def test_the_highest_id_is_leader(self):
        election = BullyElection(node_ids=(1, 2, 3, 4, 5))
        assert election.leader() == 5

    def test_failing_the_leader_promotes_the_next_highest(self):
        election = BullyElection(node_ids=(1, 2, 3, 4, 5))
        election.fail(5)
        assert election.leader() == 4


class TestElection:
    def test_a_low_initiator_is_overruled_by_a_higher_node(self):
        election = BullyElection(node_ids=(1, 2, 3, 4, 5))
        winner, overruled = election.start_election(2)
        assert winner == 5
        assert overruled

    def test_the_highest_live_initiator_wins_uncontested(self):
        election = BullyElection(node_ids=(1, 2, 3, 4, 5))
        election.fail(5)
        election.fail(4)
        winner, overruled = election.start_election(3)
        assert winner == 3
        assert not overruled


class TestRefusals:
    def test_a_down_node_cannot_start_an_election(self):
        election = BullyElection(node_ids=(1, 2, 3))
        election.fail(2)
        with pytest.raises(Invalid):
            election.start_election(2)

    def test_no_live_nodes_has_no_leader(self):
        election = BullyElection(node_ids=(1,))
        election.fail(1)
        with pytest.raises(Invalid):
            election.leader()

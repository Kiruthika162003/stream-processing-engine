from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.twophase import ABORT, COMMIT, TwoPhaseCoordinator


class TestDecision:
    def test_all_yes_commits(self):
        coord = TwoPhaseCoordinator(participants=("a", "b"))
        coord.vote("a", True)
        coord.vote("b", True)
        assert coord.decide() == COMMIT
        assert coord.outcome("a") == COMMIT

    def test_one_no_aborts_the_whole_transaction(self):
        coord = TwoPhaseCoordinator(participants=("a", "b"))
        coord.vote("a", True)
        coord.vote("b", False)
        assert coord.decide() == ABORT
        assert coord.outcome("a") == ABORT

    def test_the_decision_is_durable_and_idempotent(self):
        coord = TwoPhaseCoordinator(participants=("a",))
        coord.vote("a", True)
        assert coord.decide() == COMMIT
        assert coord.decide() == COMMIT


class TestBlockingWindow:
    def test_a_yes_voter_is_blocked_before_the_decision(self):
        coord = TwoPhaseCoordinator(participants=("a", "b"))
        coord.vote("a", True)
        assert coord.blocked() == ["a"]
        with pytest.raises(Halted) as caught:
            coord.outcome("a")
        assert "blocked" in str(caught.value)

    def test_the_decision_releases_the_blocked(self):
        coord = TwoPhaseCoordinator(participants=("a", "b"))
        coord.vote("a", True)
        coord.vote("b", True)
        coord.decide()
        assert coord.blocked() == []


class TestRefusals:
    def test_deciding_before_all_votes_is_refused(self):
        coord = TwoPhaseCoordinator(participants=("a", "b"))
        coord.vote("a", True)
        with pytest.raises(Invalid):
            coord.decide()

    def test_voting_after_the_decision_is_halted(self):
        coord = TwoPhaseCoordinator(participants=("a",))
        coord.vote("a", True)
        coord.decide()
        with pytest.raises(Halted):
            coord.vote("a", False)

    def test_an_unknown_participant_is_refused(self):
        coord = TwoPhaseCoordinator(participants=("a",))
        with pytest.raises(Invalid):
            coord.vote("z", True)

    def test_no_participants_is_refused(self):
        with pytest.raises(Invalid):
            TwoPhaseCoordinator(participants=())

from __future__ import annotations

import pytest

from rill.commands import AccountAggregate
from rill.errors import Invalid


def account() -> AccountAggregate:
    built = AccountAggregate(account_id="acct-1")
    built.handle("deposit", 100)
    return built


class TestTheGrammar:
    def test_the_command_becomes_a_fact(self):
        chosen = account()
        verdict = chosen.handle("withdraw", 30)
        assert verdict == "money-withdrawn 30; a fact now"
        assert chosen.balance() == 70

    def test_the_past_tense_command_is_refused(self):
        chosen = account()
        with pytest.raises(Invalid) as caught:
            chosen.handle("withdrawed", 10)
        assert "no right to refuse facts" in str(caught.value)

    def test_unknown_commands_are_refused(self):
        with pytest.raises(Invalid):
            account().handle("teleport", 5)


class TestTheRefusal:
    def test_insufficient_funds_is_an_answer_not_an_error(self):
        chosen = account()
        verdict = chosen.handle("withdraw", 500)
        assert verdict.startswith(
            "REFUSED: withdraw 500 against balance 100"
        )
        assert "planned for, not an error" in verdict
        assert chosen.balance() == 100

    def test_the_refusal_emits_no_fact(self):
        chosen = account()
        chosen.handle("withdraw", 500)
        assert len(chosen.events) == 1


class TestReplay:
    def test_the_facts_are_the_state(self):
        chosen = account()
        chosen.handle("withdraw", 30)
        chosen.handle("deposit", 5)
        verdict = chosen.replay_check()
        assert verdict == (
            "3 fact(s) replay to balance 75; the facts are "
            "the state"
        )

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.poison import PoisonPolicy


def policy() -> PoisonPolicy:
    return PoisonPolicy(retry_budget=2)


class TestTheBudget:
    def test_transient_failures_get_second_chances(self):
        chosen = policy()
        verdict = chosen.record_failure("p0:41", "timeout")
        assert "attempt 1 of 2" in verdict
        assert "second chances" in verdict

    def test_past_the_budget_the_stream_moves_on(self):
        chosen = policy()
        chosen.record_failure("p0:41", "bad utf8")
        chosen.record_failure("p0:41", "bad utf8")
        verdict = chosen.record_failure("p0:41", "bad utf8")
        assert verdict.startswith(
            "p0:41 QUARANTINED after 3 attempt(s)"
        )
        assert "no longer hostage" in verdict
        assert chosen.quarantined == [
            "p0:41: bad utf8 after 3 attempt(s)"
        ]

    def test_a_zero_budget_is_refused(self):
        with pytest.raises(Invalid) as caught:
            PoisonPolicy(retry_budget=0)
        assert "even honest machinery hiccups" in str(
            caught.value
        )

    def test_success_credits_the_second_chance(self):
        chosen = policy()
        chosen.record_failure("p0:41", "timeout")
        verdict = chosen.record_success("p0:41")
        assert verdict == (
            "p0:41 succeeded on attempt 2; the second chance "
            "was the right call"
        )
        assert chosen.attempts == {}


class TestTheDeployCheck:
    def test_a_few_quarantines_are_a_data_problem(self):
        chosen = policy()
        for _ in range(3):
            chosen.record_failure("p0:41", "x")
        assert "still a data problem" in chosen.deploy_check()

    def test_a_burst_of_quarantines_is_a_release(self):
        chosen = policy()
        for offset in ("a", "b", "c"):
            for _ in range(3):
                chosen.record_failure(offset, "schema")
        verdict = chosen.deploy_check()
        assert "this rate is a release" in verdict
        assert "page the deploy owner, not the data owner" in (
            verdict
        )

    def test_the_window_resets_the_suspicion(self):
        chosen = policy()
        for offset in ("a", "b", "c"):
            for _ in range(3):
                chosen.record_failure(offset, "schema")
        chosen.close_window()
        assert "still a data problem" in chosen.deploy_check()


class TestTheDlq:
    def test_the_page_lists_what_waits_for_a_human(self):
        chosen = policy()
        for _ in range(3):
            chosen.record_failure("p0:41", "bad utf8")
        page = chosen.dlq_page()
        assert page.startswith("1 record(s) waiting for a human:")
        assert "p0:41: bad utf8 after 3 attempt(s)" in page

    def test_the_empty_queue_is_enjoyed(self):
        assert policy().dlq_page() == (
            "the dead letter queue is empty; enjoy it"
        )

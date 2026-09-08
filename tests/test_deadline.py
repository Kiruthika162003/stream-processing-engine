from __future__ import annotations

import pytest

from rill.deadline import DeadlineChain
from rill.errors import Invalid


class TestTheChain:
    def test_a_generous_budget_runs_the_whole_chain(self):
        chain = DeadlineChain(total_budget=100)
        chain.attempt("parse", 10)
        chain.attempt("enrich", 20)
        chain.attempt("aggregate", 30)
        verdict = chain.verdict()
        assert verdict.startswith(
            "completed in 60 of 100, 40 to spare"
        )
        assert "honored the caller's clock" in verdict

    def test_the_doomed_stage_refuses_to_start(self):
        chain = DeadlineChain(total_budget=50)
        chain.attempt("parse", 30)
        verdict = chain.attempt("aggregate", 40)
        assert verdict.startswith("aggregate refused: needs 40")
        assert "two dead stages" in verdict
        assert chain.stages_run == ["parse"]

    def test_the_verdict_blames_the_deadline_not_the_system(self):
        chain = DeadlineChain(total_budget=50)
        chain.attempt("parse", 30)
        chain.attempt("aggregate", 40)
        verdict = chain.verdict()
        assert "deadline was unrealistic, not the system slow" in (
            verdict
        )
        assert "different bugs" in verdict

    def test_costless_stages_and_budgets_are_refused(self):
        with pytest.raises(Invalid):
            DeadlineChain(total_budget=0)
        with pytest.raises(Invalid):
            DeadlineChain(total_budget=10).attempt("x", 0)

    def test_remaining_tracks_the_spend(self):
        chain = DeadlineChain(total_budget=100)
        chain.attempt("a", 25)
        assert chain.remaining() == 75

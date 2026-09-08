from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.lagscale import ScaleDecision


def decision(**overrides) -> ScaleDecision:
    settings = {
        "current_lag": 5000,
        "arrival_rate": 100,
        "drain_per_worker": 40,
        "workers": 3,
        "state_move_ticks": 30,
        "horizon": 200,
    }
    settings.update(overrides)
    return ScaleDecision(**settings)


class TestTheInequality:
    def test_the_loan_that_pays_for_itself(self):
        verdict = decision().verdict()
        assert verdict.startswith(
            "SCALE UP: the newcomer drains 8000 over the "
            "horizon against 3000 added by its own migration, "
            "5000 net"
        )

    def test_the_move_that_costs_more_than_it_drains(self):
        verdict = decision(
            state_move_ticks=300, horizon=50
        ).verdict()
        assert verdict.startswith(
            "HOLD: migration adds 30000 while the newcomer "
            "only drains 2000"
        )
        assert "worse than none" in verdict

    def test_zero_lag_names_the_anxiety(self):
        verdict = decision(
            current_lag=0,
            arrival_rate=100,
            drain_per_worker=40,
        ).verdict()
        assert verdict == (
            "holding at zero lag; a scale-up here is "
            "anxiety, not arithmetic"
        )

    def test_nonsense_inputs_are_refused(self):
        with pytest.raises(Invalid):
            decision(horizon=0)
        with pytest.raises(Invalid):
            decision(current_lag=-1)

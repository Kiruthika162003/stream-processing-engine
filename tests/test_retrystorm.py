from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.retrystorm import RetryStorm


def storm() -> RetryStorm:
    return RetryStorm(
        base_rate=1000,
        failure_rate=0.8,
        retry_budget_share=0.1,
    )


class TestTheDynamics:
    def test_the_naive_policy_climbs_toward_the_spiral(self):
        chosen = storm()
        assert chosen.naive_peak(3) == 2952
        assert chosen.naive_peak(10) == 4569

    def test_the_budget_holds_the_multiplier_near_one(self):
        chosen = storm()
        assert chosen.budgeted_peak(10) == 1100

    def test_bad_fractions_are_refused(self):
        with pytest.raises(Invalid):
            RetryStorm(
                base_rate=100,
                failure_rate=1.5,
                retry_budget_share=0.1,
            )
        with pytest.raises(Invalid):
            RetryStorm(
                base_rate=100,
                failure_rate=0.5,
                retry_budget_share=2.0,
            )


class TestTheComparison:
    def test_the_comparison_prints_both_multipliers(self):
        verdict = storm().comparison(10)
        assert "naive peaks at 4569 (4.6x real traffic)" in verdict
        assert "budgeted peaks at 1100 (1.1x)" in verdict
        assert "death spiral" in verdict

    def test_a_zero_round_storm_is_refused(self):
        with pytest.raises(Invalid):
            storm().comparison(0)

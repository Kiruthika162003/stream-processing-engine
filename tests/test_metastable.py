from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.metastable import MetastableSystem


def system() -> MetastableSystem:
    return MetastableSystem(
        healthy_threshold=100, amplification=1.5
    )


class TestTheTwoEquilibria:
    def test_light_load_stays_healthy(self):
        chosen = system()
        assert "healthy at load 80" in chosen.offer(80)

    def test_a_spike_tips_into_the_failed_state(self):
        chosen = system()
        verdict = chosen.offer(250)
        assert "tipped into the failed equilibrium" in verdict
        assert chosen.state == "failed"

    def test_the_failed_state_sustains_itself(self):
        chosen = system()
        chosen.offer(250)
        verdict = chosen.offer(0)
        assert "the trigger is gone and the effect remains" in (
            verdict
        )
        assert chosen.state == "failed"

    def test_no_amplification_is_ordinary_overload(self):
        with pytest.raises(Invalid) as caught:
            MetastableSystem(
                healthy_threshold=100, amplification=1.0
            )
        assert "ordinary overload" in str(caught.value)


class TestEscape:
    def test_shedding_only_below_the_trigger_does_nothing(self):
        chosen = system()
        chosen.offer(250)
        verdict = chosen.shed_to(150)
        assert "did nothing" in verdict
        assert "the path back is not the path in" in verdict
        assert chosen.state == "failed"

    def test_shedding_below_the_healthy_threshold_recovers(self):
        chosen = system()
        chosen.offer(250)
        verdict = chosen.shed_to(80)
        assert "recovered" in verdict
        assert chosen.state == "healthy"

    def test_a_healthy_system_has_nothing_to_escape(self):
        assert "nothing to escape" in system().shed_to(50)

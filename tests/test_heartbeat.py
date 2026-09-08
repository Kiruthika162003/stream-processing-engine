from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.heartbeat import HeartbeatMonitor


def monitor() -> HeartbeatMonitor:
    return HeartbeatMonitor(pulse_interval=10)


class TestTheDistinction:
    def test_pulsing_but_eventless_is_quiet_not_dead(self):
        chosen = monitor()
        chosen.pulse("sensor-7", now=100)
        verdict = chosen.read("sensor-7", now=105)
        assert "healthy with nothing to say" in verdict

    def test_one_missed_pulse_does_not_declare_death(self):
        chosen = monitor()
        chosen.pulse("sensor-7", now=100)
        verdict = chosen.read("sensor-7", now=115)
        assert "DEAD" not in verdict

    def test_past_the_grace_the_verdict_is_a_fact(self):
        chosen = monitor()
        chosen.pulse("sensor-7", now=100)
        verdict = chosen.read("sensor-7", now=121)
        assert verdict.startswith(
            "sensor-7: DEAD, last pulse at 100"
        )
        assert "phrased as a fact for the oncall" in verdict

    def test_events_count_as_pulses(self):
        chosen = monitor()
        chosen.event("sensor-7", now=100)
        assert "active, last event at 100" in chosen.read(
            "sensor-7", now=105
        )

    def test_the_never_heard_source_is_not_yet_a_fact(self):
        assert "not yet a fact" in monitor().read(
            "ghost", now=50
        )


class TestTheRoll:
    def test_the_roll_names_the_dead(self):
        chosen = monitor()
        chosen.pulse("alive", now=100)
        chosen.pulse("gone", now=10)
        roll = chosen.roll(now=105)
        assert roll == "1 dead of 2: gone"

    def test_a_healthy_fleet_is_accounted_for(self):
        chosen = monitor()
        chosen.pulse("a", now=100)
        chosen.event("b", now=101)
        assert "all accounted for, quiet or loud" in (
            chosen.roll(now=105)
        )

    def test_an_empty_roll_is_refused(self):
        with pytest.raises(Invalid):
            monitor().roll(now=5)

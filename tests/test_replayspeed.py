from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.replayspeed import AcceleratedReplay


def replay() -> AcceleratedReplay:
    return AcceleratedReplay(
        events=1_000_000, event_time_span=31_000_000
    )


class TestSpeed:
    def test_a_year_does_not_take_a_year(self):
        verdict = replay().speedup(events_per_tick=1000)
        assert "accelerated 1000" in verdict
        assert "31000x" in verdict

    def test_acceleration_needs_a_positive_rate(self):
        with pytest.raises(Invalid):
            replay().accelerated_wall_time(0)

    def test_an_empty_replay_is_refused(self):
        with pytest.raises(Invalid):
            AcceleratedReplay(events=0, event_time_span=10)


class TestSafety:
    def test_the_clean_replay_equals_the_original(self):
        assert "replay-safe: nothing read wall time" in (
            replay().safety_report()
        )

    def test_a_wall_clock_read_is_flagged_unsafe(self):
        chosen = replay()
        verdict = chosen.flag_wall_clock("session-ttl-cache")
        assert "replay-unsafe" in verdict
        assert "nobody can trust" in verdict

    def test_the_safety_report_names_the_offenders(self):
        chosen = replay()
        chosen.flag_wall_clock("session-ttl-cache")
        chosen.flag_wall_clock("rate-limiter")
        report = chosen.safety_report()
        assert "2 replay-unsafe operation(s)" in report
        assert "session-ttl-cache, rate-limiter" in report
        assert "the clock the replay sped past" in report

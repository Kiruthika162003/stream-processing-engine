from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.timingwheel import TimingWheel


def _fire_tick(wheel: TimingWheel, item: str, horizon: int) -> int:
    for tick in range(1, horizon + 1):
        if item in wheel.advance():
            return tick
    return -1


class TestFiring:
    def test_a_timer_fires_at_its_scheduled_tick(self):
        wheel = TimingWheel(slots=8)
        wheel.schedule(3, "a")
        assert _fire_tick(wheel, "a", 8) == 3

    def test_timers_in_the_same_slot_both_fire(self):
        wheel = TimingWheel(slots=8)
        wheel.schedule(3, "a")
        wheel.schedule(3, "b")
        assert set(wheel.advance() + wheel.advance() + wheel.advance()) == {"a", "b"}

    def test_a_delay_beyond_the_wheel_uses_the_rounds_counter(self):
        wheel = TimingWheel(slots=4)
        wheel.schedule(7, "x")  # wraps once plus three
        assert _fire_tick(wheel, "x", 10) == 7

    def test_pending_counts_the_unfired(self):
        wheel = TimingWheel(slots=8)
        wheel.schedule(3, "a")
        wheel.schedule(5, "b")
        assert wheel.pending() == 2
        wheel.advance()
        wheel.advance()
        wheel.advance()  # fires a
        assert wheel.pending() == 1


class TestRefusals:
    def test_a_nonpositive_slot_count_is_refused(self):
        with pytest.raises(Invalid):
            TimingWheel(slots=0)

    def test_a_delay_below_one_is_refused(self):
        with pytest.raises(Invalid):
            TimingWheel(slots=8).schedule(0, "a")

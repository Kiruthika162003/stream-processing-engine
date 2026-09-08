from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.timers import TimerService


def service() -> TimerService:
    return TimerService()


class TestSettingAndClearing:
    def test_a_timer_awaits_the_silence(self):
        chosen = service()
        assert chosen.set_timer("cart-7", 30) == (
            "cart-7: timer set for 30"
        )

    def test_resetting_replaces_instead_of_stacking(self):
        chosen = service()
        chosen.set_timer("cart-7", 30)
        verdict = chosen.set_timer("cart-7", 45)
        assert "deadline moves 30 -> 45" in verdict
        assert "replaced, not stacked" in verdict
        assert chosen.replaced == 1

    def test_the_awaited_thing_clears_the_timer(self):
        chosen = service()
        chosen.set_timer("cart-7", 30)
        assert "timer cleared" in chosen.clear("cart-7")
        with pytest.raises(Invalid):
            chosen.clear("cart-7")

    def test_keyless_and_negative_timers_are_refused(self):
        with pytest.raises(Invalid):
            service().set_timer("", 5)
        with pytest.raises(Invalid):
            service().set_timer("k", -1)


class TestFiring:
    def test_the_watermark_matures_timers_in_order(self):
        chosen = service()
        chosen.set_timer("late-cart", 20)
        chosen.set_timer("later-cart", 25)
        chosen.set_timer("patient", 90)
        firings = chosen.advance(watermark=30)
        assert firings == [
            "late-cart: silence lasted to 20; firing",
            "later-cart: silence lasted to 25; firing",
        ]
        assert "patient" in chosen.deadlines

    def test_the_storm_is_measured_at_its_peak(self):
        chosen = service()
        for number in range(50):
            chosen.set_timer(f"k{number}", 10 + number % 3)
        chosen.advance(watermark=100)
        report = chosen.storm_report()
        assert "50 firing(s), largest herd 50" in report
        assert "the jump, not the average" in report

    def test_a_cleared_timer_never_fires(self):
        chosen = service()
        chosen.set_timer("cart-7", 20)
        chosen.clear("cart-7")
        assert chosen.advance(watermark=99) == []

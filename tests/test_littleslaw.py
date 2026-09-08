from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.littleslaw import LittleSizer


def sizer() -> LittleSizer:
    return LittleSizer(arrival_rate=200)


class TestBothDirections:
    def test_the_buffer_is_the_product(self):
        verdict = sizer().buffer_for_delay(tolerable_delay=5)
        assert "rate 200 x delay 5 = buffer 1000" in verdict
        assert "stored delay" in verdict

    def test_occupancy_reads_as_residence(self):
        verdict = sizer().delay_from_occupancy(occupancy=900)
        assert "means 4.5 tick(s) of residence" in verdict
        assert "delay meter reading near its maximum" in verdict

    def test_degenerate_inputs_are_refused(self):
        with pytest.raises(Invalid):
            LittleSizer(arrival_rate=0)
        with pytest.raises(Invalid):
            sizer().buffer_for_delay(0)


class TestStability:
    def test_the_stable_queue_sits_inside_the_law(self):
        verdict = sizer().stability_check(
            occupancy=900, expected_residence=5
        )
        assert verdict == (
            "stable: occupancy 900 within the law's 1000"
        )

    def test_the_polite_word_for_falling_behind(self):
        verdict = sizer().stability_check(
            occupancy=1500, expected_residence=5
        )
        assert verdict.startswith("UNSTABLE: occupancy 1500")
        assert "Little's polite word for falling behind" in (
            verdict
        )

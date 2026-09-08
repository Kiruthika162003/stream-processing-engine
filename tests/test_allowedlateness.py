from __future__ import annotations

import pytest

from rill.allowedlateness import LatenessWindow
from rill.errors import Invalid


def window() -> LatenessWindow:
    return LatenessWindow(window_end=100, allowed_lateness=20)


class TestFiringAndCorrecting:
    def test_the_window_fires_when_the_watermark_passes(self):
        chosen = window()
        chosen.add(5, watermark=50)
        assert chosen.add(3, watermark=100) == "fire: total 8"

    def test_the_straggler_re_fires_as_a_correction(self):
        chosen = window()
        chosen.add(5, watermark=100)
        verdict = chosen.add(2, watermark=110)
        assert verdict.startswith("re-fire (CORRECTION): total now 7")
        assert "within the grace" in verdict

    def test_negative_lateness_is_refused(self):
        with pytest.raises(Invalid):
            LatenessWindow(window_end=100, allowed_lateness=-1)


class TestDropping:
    def test_the_grace_holds_until_it_expires(self):
        chosen = window()
        assert "grace holds, 10 tick(s)" in chosen.maybe_drop(
            watermark=110
        )

    def test_the_state_drops_after_the_grace(self):
        chosen = window()
        chosen.add(5, watermark=100)
        verdict = chosen.maybe_drop(watermark=125)
        assert "state dropped at watermark 125" in verdict
        assert "memory held past usefulness" in verdict

    def test_a_too_late_event_is_a_real_dropped_update(self):
        chosen = window()
        chosen.add(5, watermark=100)
        chosen.maybe_drop(watermark=125)
        verdict = chosen.add(9, watermark=130)
        assert "a real dropped update, not a rounding error" in (
            verdict
        )
        assert chosen.dropped_updates == 1

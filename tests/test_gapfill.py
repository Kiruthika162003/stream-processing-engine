from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.gapfill import GapFiller

OBSERVED = {0: 12, 10: 7, 30: 9}


class TestTheDistinction:
    def test_the_gap_renders_as_a_gap_not_a_number(self):
        filler = GapFiller(window_size=10, policy="render-gap")
        series = filler.fill(OBSERVED, 0, 30)
        assert series[2].startswith("[20): GAP")
        assert "different facts" in series[2]

    def test_zero_fill_stamps_its_fills_synthetic(self):
        filler = GapFiller(window_size=10, policy="zero-fill")
        series = filler.fill(OBSERVED, 0, 30)
        assert series[2].startswith("[20): 0 (synthetic")

    def test_carry_forward_holds_the_last_gauge(self):
        filler = GapFiller(
            window_size=10, policy="carry-forward"
        )
        series = filler.fill(OBSERVED, 0, 30)
        assert series[2] == (
            "[20): 7 (synthetic; gauge carried forward)"
        )

    def test_carry_forward_with_nothing_to_carry_is_a_gap(self):
        filler = GapFiller(
            window_size=10, policy="carry-forward"
        )
        series = filler.fill({10: 5}, 0, 10)
        assert series[0] == "[0): GAP (nothing to carry)"

    def test_real_windows_pass_through_untouched(self):
        filler = GapFiller(window_size=10, policy="render-gap")
        series = filler.fill(OBSERVED, 0, 30)
        assert series[0] == "[0): 12"
        assert series[3] == "[30): 9"

    def test_bad_policies_and_ranges_are_refused(self):
        with pytest.raises(Invalid):
            GapFiller(window_size=10, policy="interpolate")
        with pytest.raises(Invalid):
            GapFiller(
                window_size=10, policy="render-gap"
            ).fill(OBSERVED, 30, 0)


class TestTheOutageCheck:
    def test_wide_silence_is_named_a_broken_collector(self):
        filler = GapFiller(window_size=10, policy="render-gap")
        verdict = filler.outage_check(
            OBSERVED, expected_windows=10
        )
        assert "broken collector wearing a quiet night's" in (
            verdict
        )

    def test_narrow_silence_earns_one_glance(self):
        filler = GapFiller(window_size=10, policy="render-gap")
        verdict = filler.outage_check(
            OBSERVED, expected_windows=4
        )
        assert "worth one glance" in verdict

    def test_full_attendance_is_healthy(self):
        filler = GapFiller(window_size=10, policy="render-gap")
        assert "collector is healthy" in filler.outage_check(
            OBSERVED, expected_windows=3
        )

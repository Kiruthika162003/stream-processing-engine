from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.windowcost import WindowConfig, comparison_page

COARSE = WindowConfig(
    label="five-minute tumbling",
    window_size=300,
    slide=300,
    active_keys=1000,
    horizon=3600,
)
SMOOTH = WindowConfig(
    label="five-minute sliding by thirty",
    window_size=300,
    slide=30,
    active_keys=1000,
    horizon=3600,
)


class TestTheBill:
    def test_tumbling_holds_one_pane_per_key(self):
        assert COARSE.panes_per_key() == 1
        assert COARSE.live_panes() == 1000
        assert "nobody remembers approving" not in COARSE.bill()

    def test_the_sliding_multiplier_is_the_surprise(self):
        assert SMOOTH.panes_per_key() == 10
        bill = SMOOTH.bill()
        assert "10000 live pane(s)" in bill
        assert "costs 10x the tumbling bill" in bill
        assert "nobody remembers approving" in bill

    def test_firings_scale_with_the_slide(self):
        assert COARSE.firings_over_horizon() == 12 * 1000
        assert SMOOTH.firings_over_horizon() == 120 * 1000

    def test_gappy_and_degenerate_configs_are_refused(self):
        with pytest.raises(Invalid):
            WindowConfig(
                label="x",
                window_size=10,
                slide=20,
                active_keys=1,
                horizon=100,
            )


class TestThePage:
    def test_the_page_ends_with_the_ratio(self):
        page = comparison_page([COARSE, SMOOTH])
        assert page.splitlines()[-1] == (
            "five-minute sliding by thirty holds 10x the "
            "state of five-minute tumbling"
        )

    def test_a_single_candidate_is_not_a_comparison(self):
        with pytest.raises(Invalid):
            comparison_page([COARSE])

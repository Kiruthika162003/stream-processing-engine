from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.freshness import FreshnessWaterfall


def waterfall() -> FreshnessWaterfall:
    built = FreshnessWaterfall(slo=60)
    built.allocate("ingest", 5)
    built.allocate("shuffle", 10)
    built.allocate("window-wait", 20)
    built.allocate("sink-flush", 15)
    return built


class TestTheBudget:
    def test_allocations_leave_margin_for_the_bad_day(self):
        built = waterfall()
        verdict = built.allocate("query-cache", 3)
        assert "margin 7 remains for the bad day" in verdict

    def test_the_zero_margin_split_is_refused(self):
        built = waterfall()
        with pytest.raises(Invalid) as caught:
            built.allocate("greedy-stage", 9)
        assert "the sentence every SLO owner learns once" in (
            str(caught.value)
        )

    def test_spending_needs_an_allocation(self):
        with pytest.raises(Invalid):
            waterfall().spend("mystery", 5)


class TestTheReport:
    def test_the_overspender_is_a_config_change(self):
        built = waterfall()
        built.spend("ingest", 4)
        built.spend("shuffle", 8)
        built.spend("window-wait", 18)
        built.spend("sink-flush", 40)
        report = built.waterfall_report()
        assert "sink-flush: 40 of 15 OVER by 25" in report
        assert "end to end: 70 of 60" in report
        assert (
            "the overspender is sink-flush, a config change"
        ) in report

    def test_a_healthy_waterfall_has_no_overspender(self):
        built = waterfall()
        for stage, spent in (
            ("ingest", 4),
            ("shuffle", 8),
            ("window-wait", 18),
            ("sink-flush", 12),
        ):
            built.spend(stage, spent)
        report = built.waterfall_report()
        assert "OVER" not in report
        assert "end to end: 42 of 60" in report

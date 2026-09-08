from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.watermarklag import WatermarkLag


def tracker() -> WatermarkLag:
    return WatermarkLag(lateness_bound=10, freshness_sla=30)


class TestTheLag:
    def test_lag_is_wall_clock_minus_watermark(self):
        assert tracker().lag(now=100, watermark=75) == 25

    def test_the_watermark_cannot_lead_wall_clock(self):
        with pytest.raises(Invalid):
            tracker().lag(now=100, watermark=120)

    def test_bad_configuration_is_refused(self):
        with pytest.raises(Invalid):
            WatermarkLag(lateness_bound=-1, freshness_sla=10)


class TestTheDiagnosis:
    def test_within_sla_finalizes_on_time(self):
        verdict = tracker().diagnose(
            now=100, watermark=80, slowest_source=95
        )
        assert "within the 30 SLA" in verdict

    def test_a_straggling_source_is_an_incident(self):
        verdict = tracker().diagnose(
            now=100, watermark=40, slowest_source=45
        )
        assert "straggling source" in verdict
        assert "not the bound you set on purpose" in verdict

    def test_the_bound_is_a_deliberate_tradeoff(self):
        verdict = tracker().diagnose(
            now=100, watermark=60, slowest_source=98
        )
        assert "lateness bound" in verdict
        assert "a correctness-latency tradeoff you chose" in (
            verdict
        )

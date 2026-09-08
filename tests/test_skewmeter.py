from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.skewmeter import SkewMeter


def measured_week() -> SkewMeter:
    meter = SkewMeter()
    for number in range(95):
        meter.observe(event_time=100, arrival=100 + number % 4)
    for _ in range(5):
        meter.observe(event_time=100, arrival=112)
    return meter


class TestTheDistribution:
    def test_skew_is_arrival_minus_event_time(self):
        meter = SkewMeter()
        meter.observe(event_time=10, arrival=17)
        assert meter.skews == [7]

    def test_a_lying_clock_is_a_different_meter(self):
        with pytest.raises(Invalid) as caught:
            SkewMeter().observe(event_time=10, arrival=5)
        assert "a different meter" in str(caught.value)

    def test_percentiles_read_the_recorded_truth(self):
        meter = measured_week()
        assert meter.percentile(50) <= 3
        assert meter.percentile(99) == 12


class TestTheWhatIf:
    def test_each_bound_prices_its_refusals(self):
        meter = measured_week()
        assert meter.refusal_share(3) == 5.0
        assert meter.refusal_share(12) == 0.0

    def test_the_table_replaces_the_outage_story(self):
        table = measured_week().what_if_table([3, 12])
        assert "bound 3 refuses 5.0%" in table
        assert "bound 12 refuses 0.0%" in table
        assert "not from the best outage story" in table
        assert "re-sized when they breathe" in table

    def test_empty_meters_and_tables_are_refused(self):
        with pytest.raises(Invalid):
            SkewMeter().percentile(50)
        with pytest.raises(Invalid):
            measured_week().what_if_table([])

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.fanout import FanOut


def three_sinks() -> FanOut:
    fan = FanOut()
    for sink in ("alerts", "warehouse", "archive"):
        fan.subscribe(sink)
    fan.publish(count=1000)
    fan.advance("alerts", 990)
    fan.advance("archive", 800)
    fan.advance("warehouse", 200)
    return fan


class TestIndependence:
    def test_each_sink_reads_at_its_own_pace(self):
        fan = three_sinks()
        assert fan.positions["alerts"] == 990
        assert fan.positions["warehouse"] == 200

    def test_nobody_reads_backwards_or_ahead(self):
        fan = three_sinks()
        with pytest.raises(Invalid):
            fan.advance("alerts", 5)
        with pytest.raises(Invalid):
            fan.advance("alerts", 2000)

    def test_double_subscription_is_refused(self):
        fan = three_sinks()
        with pytest.raises(Invalid):
            fan.subscribe("alerts")


class TestTheSpread:
    def test_the_hostage_line_has_an_owner(self):
        report = three_sinks().spread_report()
        assert report.startswith("3 sink(s), spread 790")
        assert (
            "warehouse is 800 event(s) behind the head and "
            "anchors the tail"
        ) in report
        assert "the-topic-is-big has none" in report

    def test_no_subscribers_no_spread(self):
        with pytest.raises(Invalid):
            FanOut().spread_report()


class TestDetaching:
    def test_detaching_needs_its_reason(self):
        fan = three_sinks()
        with pytest.raises(Invalid) as caught:
            fan.detach("archive", "  ")
        assert "everyone forgot" in str(caught.value)

    def test_the_detached_sink_stops_anchoring(self):
        fan = three_sinks()
        fan.detach(
            "warehouse", "loader migrated to the new topic"
        )
        report = fan.spread_report()
        assert "archive is 200 event(s) behind" in report
        assert fan.detached == [
            "warehouse: loader migrated to the new topic"
        ]

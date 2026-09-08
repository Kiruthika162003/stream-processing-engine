from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.gaugestream import Metric, aggregate


class TestCounters:
    def test_a_counter_sums_across_shards(self):
        requests = Metric(name="requests", shape="counter")
        assert aggregate(requests, [100, 200, 300], "sum") == (
            "requests total: 600"
        )

    def test_averaging_a_counter_loses_the_total(self):
        requests = Metric(name="requests", shape="counter")
        with pytest.raises(Invalid) as caught:
            aggregate(requests, [100, 200], "average")
        assert "loses the total it exists to report" in str(
            caught.value
        )


class TestGauges:
    def test_summing_a_gauge_is_the_climbing_dashboard(self):
        memory = Metric(name="memory", shape="gauge")
        with pytest.raises(Invalid) as caught:
            aggregate(memory, [500, 500, 500], "sum")
        assert "grows with shard count for no reason" in str(
            caught.value
        )

    def test_a_gauge_averages_to_a_representative_value(self):
        memory = Metric(name="memory", shape="gauge")
        assert aggregate(memory, [400, 500, 600], "average") == (
            "memory typical: 500 (averaged, the representative "
            "value)"
        )

    def test_a_gauge_can_take_the_latest(self):
        memory = Metric(name="memory", shape="gauge")
        assert "latest: 600" in aggregate(
            memory, [400, 500, 600], "latest"
        )


class TestRefusals:
    def test_an_unknown_shape_is_refused(self):
        with pytest.raises(Invalid):
            Metric(name="x", shape="vibes")

    def test_nothing_to_aggregate_is_refused(self):
        with pytest.raises(Invalid):
            aggregate(
                Metric(name="m", shape="counter"), [], "sum"
            )

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.shuffle import ShufflePlanner


class TestRouting:
    def test_the_owner_node_is_deterministic(self):
        planner = ShufflePlanner(consumer_nodes=4)
        assert planner.owner_node("user-1") == planner.owner_node(
            "user-1"
        )

    def test_a_co_located_key_never_touches_the_wire(self):
        planner = ShufflePlanner(consumer_nodes=4)
        key = "user-1"
        owner = planner.owner_node(key)
        verdict = planner.route(key, producer_node=owner)
        assert "co-located on node" in verdict
        assert planner.same_node == 1

    def test_a_cross_node_key_crosses_the_wire(self):
        planner = ShufflePlanner(consumer_nodes=4)
        key = "user-1"
        owner = planner.owner_node(key)
        other = (owner + 1) % 4
        verdict = planner.route(key, producer_node=other)
        assert "crosses the wire" in verdict
        assert planner.cross_node == 1

    def test_consumerless_shuffles_are_refused(self):
        with pytest.raises(Invalid):
            ShufflePlanner(consumer_nodes=0)


class TestTheCostReport:
    def test_a_mostly_cross_node_shuffle_is_a_network_bill(self):
        planner = ShufflePlanner(consumer_nodes=4)
        for number in range(100):
            key = f"user-{number}"
            owner = planner.owner_node(key)
            planner.route(key, producer_node=(owner + 1) % 4)
        report = planner.cost_report()
        assert "100% on the wire" in report
        assert "a network bill" in report

    def test_a_co_located_shuffle_buys_nothing(self):
        planner = ShufflePlanner(consumer_nodes=4)
        for number in range(100):
            key = f"user-{number}"
            planner.route(key, producer_node=planner.owner_node(key))
        report = planner.cost_report()
        assert "0% on the wire" in report
        assert "buying bandwidth here buys nothing" in report

    def test_an_empty_shuffle_is_refused(self):
        with pytest.raises(Invalid):
            ShufflePlanner(consumer_nodes=4).cost_report()

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.maxflow import max_flow


class TestFlow:
    def test_the_classic_network(self):
        graph = {"s": {"a": 10, "b": 10}, "a": {"b": 2, "t": 8}, "b": {"t": 10}}
        assert max_flow(graph, "s", "t") == 18

    def test_no_path_carries_no_flow(self):
        graph = {"s": {"a": 5}, "b": {"t": 5}}
        assert max_flow(graph, "s", "t") == 0


class TestMinCut:
    def test_flow_is_capped_by_the_bottleneck(self):
        graph = {"s": {"a": 5}, "a": {"t": 100}}
        assert max_flow(graph, "s", "t") == 5

    def test_raising_a_non_bottleneck_edge_does_nothing(self):
        graph = {"s": {"a": 5}, "a": {"t": 1000}}
        assert max_flow(graph, "s", "t") == 5

    def test_raising_the_bottleneck_edge_lifts_the_flow(self):
        graph = {"s": {"a": 50}, "a": {"t": 100}}
        assert max_flow(graph, "s", "t") == 50


class TestRefusals:
    def test_source_equal_to_sink_is_refused(self):
        with pytest.raises(Invalid):
            max_flow({"s": {}}, "s", "s")

    def test_a_negative_capacity_is_refused(self):
        with pytest.raises(Invalid):
            max_flow({"s": {"t": -1}}, "s", "t")

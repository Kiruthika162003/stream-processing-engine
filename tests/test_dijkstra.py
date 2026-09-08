from __future__ import annotations

import pytest

from rill.dijkstra import shortest_path
from rill.errors import Invalid, Missing

GRAPH = {
    "A": [("B", 1), ("C", 4)],
    "B": [("C", 2), ("D", 5)],
    "C": [("D", 1)],
    "D": [],
}


class TestShortestPath:
    def test_it_finds_the_lowest_cost_route(self):
        distance, path = shortest_path(GRAPH, "A", "D")
        assert distance == 4
        assert path == ["A", "B", "C", "D"]

    def test_it_prefers_a_cheaper_multi_hop_over_a_direct_edge(self):
        distance, path = shortest_path(GRAPH, "A", "C")
        assert distance == 3  # A-B-C beats the direct A-C of 4
        assert path == ["A", "B", "C"]

    def test_source_to_itself_is_zero(self):
        assert shortest_path(GRAPH, "A", "A") == (0, ["A"])


class TestRefusals:
    def test_no_path_is_missing(self):
        graph = {"A": [], "B": []}
        with pytest.raises(Missing):
            shortest_path(graph, "A", "B")

    def test_a_negative_weight_is_refused(self):
        graph = {"A": [("B", -1)], "B": []}
        with pytest.raises(Invalid):
            shortest_path(graph, "A", "B")

    def test_an_unknown_source_is_refused(self):
        with pytest.raises(Invalid):
            shortest_path(GRAPH, "Z", "A")

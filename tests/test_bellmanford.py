from __future__ import annotations

import pytest

from rill.bellmanford import distance_to, shortest_distance
from rill.errors import Halted, Invalid, Missing

NODES = ["A", "B", "C", "D"]
EDGES = [("A", "B", 1), ("B", "C", -2), ("A", "C", 4), ("C", "D", 1)]


class TestNegativeEdges:
    def test_it_routes_through_a_negative_edge(self):
        assert distance_to(NODES, EDGES, "A", "D") == 0  # 1 - 2 + 1
        assert distance_to(NODES, EDGES, "A", "C") == -1  # 1 - 2

    def test_the_source_is_zero(self):
        assert distance_to(NODES, EDGES, "A", "A") == 0


class TestNegativeCycle:
    def test_a_negative_cycle_is_halted(self):
        cycle = [("A", "B", 1), ("B", "C", -3), ("C", "A", 1)]
        with pytest.raises(Halted):
            shortest_distance(["A", "B", "C"], cycle, "A")


class TestRefusals:
    def test_an_unreachable_target_is_missing(self):
        nodes = ["A", "B"]
        with pytest.raises(Missing):
            distance_to(nodes, [], "A", "B")

    def test_an_unknown_source_is_refused(self):
        with pytest.raises(Invalid):
            shortest_distance(NODES, EDGES, "Z")

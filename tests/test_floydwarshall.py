from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.floydwarshall import INF, all_pairs

NODES = ["A", "B", "C", "D"]
EDGES = [("A", "B", 3), ("B", "C", 1), ("A", "C", 5), ("C", "D", 2)]


class TestDistances:
    def test_it_prefers_a_cheaper_route_through_a_waypoint(self):
        dist = all_pairs(NODES, EDGES)
        assert dist["A"]["C"] == 4  # A-B-C beats the direct 5

    def test_it_chains_waypoints(self):
        dist = all_pairs(NODES, EDGES)
        assert dist["A"]["D"] == 6  # A-B-C-D
        assert dist["B"]["D"] == 3

    def test_an_unreachable_pair_is_infinite(self):
        dist = all_pairs(NODES, EDGES)
        assert dist["D"]["A"] == INF

    def test_a_node_reaches_itself_at_zero(self):
        dist = all_pairs(NODES, EDGES)
        assert dist["A"]["A"] == 0


class TestNegativeCycle:
    def test_a_negative_cycle_is_halted(self):
        with pytest.raises(Halted):
            all_pairs(["X", "Y"], [("X", "Y", 1), ("Y", "X", -3)])


class TestRefusals:
    def test_no_nodes_is_refused(self):
        with pytest.raises(Invalid):
            all_pairs([], [])

    def test_an_edge_naming_an_unknown_node_is_refused(self):
        with pytest.raises(Invalid):
            all_pairs(["A"], [("A", "Z", 1)])

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.toposort import topological_order


class TestOrder:
    def test_dependencies_come_before_dependents(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]
        order = topological_order(nodes, edges)
        position = {node: index for index, node in enumerate(order)}
        assert all(position[before] < position[after] for before, after in edges)

    def test_ties_break_deterministically_by_name(self):
        nodes = ["C", "A", "B"]
        assert topological_order(nodes, []) == ["A", "B", "C"]

    def test_a_single_node_is_its_own_order(self):
        assert topological_order(["X"], []) == ["X"]


class TestRefusals:
    def test_a_cycle_has_no_order(self):
        with pytest.raises(Invalid) as caught:
            topological_order(["A", "B"], [("A", "B"), ("B", "A")])
        assert "cycle" in str(caught.value)

    def test_an_edge_naming_an_unknown_stage_is_refused(self):
        with pytest.raises(Invalid):
            topological_order(["A"], [("A", "ghost")])

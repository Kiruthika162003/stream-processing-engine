from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.scc import strongly_connected_components


def _sorted(components: list[set[str]]) -> list[list[str]]:
    return sorted(sorted(component) for component in components)


class TestComponents:
    def test_it_finds_the_maximal_cycles(self):
        nodes = ["A", "B", "C", "D", "E"]
        edges = [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
            ("C", "D"),
            ("D", "E"),
            ("E", "D"),
        ]
        assert _sorted(strongly_connected_components(nodes, edges)) == [
            ["A", "B", "C"],
            ["D", "E"],
        ]

    def test_an_acyclic_graph_is_all_singletons(self):
        components = strongly_connected_components(
            ["X", "Y", "Z"], [("X", "Y"), ("Y", "Z")]
        )
        assert all(len(component) == 1 for component in components)
        assert len(components) == 3

    def test_a_self_loop_is_its_own_component(self):
        components = strongly_connected_components(["A"], [("A", "A")])
        assert _sorted(components) == [["A"]]

    def test_the_components_partition_the_nodes(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B"), ("B", "A"), ("C", "D")]
        components = strongly_connected_components(nodes, edges)
        covered: set[str] = set()
        for component in components:
            covered |= component
        assert covered == set(nodes)


class TestRefusals:
    def test_an_edge_naming_an_unknown_node_is_refused(self):
        with pytest.raises(Invalid):
            strongly_connected_components(["A"], [("A", "Z")])

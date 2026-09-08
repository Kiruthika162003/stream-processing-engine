from __future__ import annotations

import itertools
import random

import pytest

from rill.bridges import find_bridges
from rill.errors import Invalid


def _brute(nodes: list[str], edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    def components(es: list[tuple[str, str]]) -> int:
        parent = {n: n for n in nodes}

        def find(x: str) -> str:
            while parent[x] != x:
                x = parent[x]
            return x

        for a, b in es:
            parent[find(a)] = find(b)
        return len({find(n) for n in nodes})

    base = components(edges)
    bridges = []
    for edge in edges:
        if components([e for e in edges if e != edge]) > base:
            bridges.append(tuple(sorted(edge)))
    return sorted(set(bridges))


class TestBridges:
    def test_a_cycle_has_no_bridges_but_the_tail_edges_do(self):
        nodes = ["A", "B", "C", "D", "E"]
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D"), ("D", "E")]
        assert find_bridges(nodes, edges) == [("C", "D"), ("D", "E")]

    def test_a_triangle_has_no_bridges(self):
        assert find_bridges(["A", "B", "C"], [("A", "B"), ("B", "C"), ("C", "A")]) == []

    def test_a_lone_edge_is_a_bridge(self):
        assert find_bridges(["A", "B"], [("A", "B")]) == [("A", "B")]

    def test_it_matches_brute_force(self):
        rng = random.Random(3)
        for _ in range(300):
            nodes = [str(i) for i in range(rng.randint(1, 7))]
            edges = [
                (a, b)
                for a, b in itertools.combinations(nodes, 2)
                if rng.random() < 0.4
            ]
            assert find_bridges(nodes, edges) == _brute(nodes, edges)


class TestRefusals:
    def test_an_edge_naming_an_unknown_node_is_refused(self):
        with pytest.raises(Invalid):
            find_bridges(["A"], [("A", "Z")])

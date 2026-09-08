from __future__ import annotations

import itertools
import random

import pytest

from rill.errors import Invalid, Missing
from rill.mst import mst_weight


def _brute(nodes: list[str], edges: list[tuple[str, str, int]]) -> int | None:
    best = None
    need = len(nodes) - 1
    for combo in itertools.combinations(edges, need):
        parent = {node: node for node in nodes}

        def root(x, parent=parent):
            while parent[x] != x:
                x = parent[x]
            return x

        total = 0
        for a, b, w in combo:
            ra, rb = root(a), root(b)
            if ra != rb:
                parent[ra] = rb
                total += w
        if len({root(n) for n in nodes}) == 1 and (best is None or total < best):
            best = total
    return best


class TestKruskal:
    def test_the_classic_tree(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B", 1), ("B", "C", 2), ("A", "C", 2), ("C", "D", 3), ("B", "D", 5)]
        assert mst_weight(nodes, edges) == 6

    def test_a_single_node_needs_no_edges(self):
        assert mst_weight(["X"], []) == 0

    def test_it_matches_brute_force(self):
        rng = random.Random(5)
        for _ in range(200):
            n = rng.randint(2, 6)
            nodes = [str(i) for i in range(n)]
            edges = []
            for a, b in itertools.combinations(nodes, 2):
                if rng.random() < 0.6:
                    edges.append((a, b, rng.randint(1, 20)))
            expected = _brute(nodes, edges)
            if expected is None:
                with pytest.raises(Missing):
                    mst_weight(nodes, edges)
            else:
                assert mst_weight(nodes, edges) == expected


class TestRefusals:
    def test_a_disconnected_graph_has_no_tree(self):
        with pytest.raises(Missing):
            mst_weight(["A", "B"], [])

    def test_no_nodes_is_refused(self):
        with pytest.raises(Invalid):
            mst_weight([], [])

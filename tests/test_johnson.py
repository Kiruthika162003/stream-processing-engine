from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.johnson import all_pairs

INF = float("inf")


def _floyd(nodes, edges):
    d = {u: {v: (0.0 if u == v else INF) for v in nodes} for u in nodes}
    for u, v, w in edges:
        d[u][v] = min(d[u][v], w)
    for k in nodes:
        for i in nodes:
            for j in nodes:
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d


class TestAllPairs:
    def test_a_negative_edge_no_cycle(self):
        nodes = [0, 1, 2, 3]
        edges = [(0, 1, -2), (1, 2, 3), (2, 3, 1), (0, 3, 10), (0, 2, 4)]
        ap = all_pairs(nodes, edges)
        assert ap[0][3] == 2.0  # 0 -> 1 -> 2 -> 3 is -2 + 3 + 1
        assert ap[0][0] == 0.0

    def test_it_matches_floyd_warshall_including_negative_edges(self):
        rng = random.Random(73)
        tested = 0
        for _ in range(1500):
            n = rng.randint(1, 7)
            nodes = list(range(n))
            edges = [
                (u, v, rng.randint(-3, 8))
                for u in nodes
                for v in nodes
                if u != v and rng.random() < 0.4
            ]
            try:
                got = all_pairs(nodes, edges)
            except Invalid:
                continue  # negative cycle; Johnson correctly refuses
            tested += 1
            fw = _floyd(nodes, edges)
            for u in nodes:
                for v in nodes:
                    assert got[u].get(v, INF) == fw[u][v]
        assert tested > 500


class TestRefusals:
    def test_a_negative_cycle_is_refused(self):
        with pytest.raises(Invalid):
            all_pairs([0, 1], [(0, 1, -1), (1, 0, -1)])

    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            all_pairs(None, [])

    def test_an_edge_to_an_unlisted_node_is_refused(self):
        with pytest.raises(Invalid):
            all_pairs([0], [(0, 5, 1.0)])

from __future__ import annotations

import random
from collections import deque

import pytest

from rill.dinic import Dinic
from rill.errors import Invalid


def _brute_maxflow(n, edges, s, t):
    cap = [[0] * n for _ in range(n)]
    for u, v, c in edges:
        cap[u][v] += c
    flow = 0
    while True:
        parent = [-1] * n
        parent[s] = s
        q = deque([s])
        while q:
            u = q.popleft()
            for v in range(n):
                if parent[v] == -1 and cap[u][v] > 0:
                    parent[v] = u
                    q.append(v)
        if parent[t] == -1:
            break
        b = float("inf")
        v = t
        while v != s:
            b = min(b, cap[parent[v]][v])
            v = parent[v]
        v = t
        while v != s:
            cap[parent[v]][v] -= b
            cap[v][parent[v]] += b
            v = parent[v]
        flow += b
    return flow


class TestMaxFlow:
    def test_the_classic_network(self):
        d = Dinic(4)
        for u, v, c in [(0, 1, 3), (0, 2, 2), (1, 2, 1), (1, 3, 2), (2, 3, 4)]:
            d.add_edge(u, v, c)
        assert d.max_flow(0, 3) == 5

    def test_a_single_bottleneck_limits_the_flow(self):
        d = Dinic(4)
        d.add_edge(0, 1, 100)
        d.add_edge(1, 2, 1)  # the bottleneck
        d.add_edge(2, 3, 100)
        assert d.max_flow(0, 3) == 1

    def test_it_matches_edmonds_karp_on_random_networks(self):
        rng = random.Random(97)
        for _ in range(2000):
            n = rng.randint(2, 7)
            edges = [
                (u, v, rng.randint(0, 10))
                for u in range(n)
                for v in range(n)
                if u != v and rng.random() < 0.4
            ]
            d = Dinic(n)
            for u, v, c in edges:
                d.add_edge(u, v, c)
            assert d.max_flow(0, n - 1) == _brute_maxflow(n, edges, 0, n - 1)


class TestRefusals:
    def test_a_non_positive_node_count_is_refused(self):
        with pytest.raises(Invalid):
            Dinic(0)

    def test_an_out_of_range_edge_is_refused(self):
        with pytest.raises(Invalid):
            Dinic(3).add_edge(0, 9, 1)

    def test_equal_source_and_sink_is_refused(self):
        with pytest.raises(Invalid):
            Dinic(3).max_flow(1, 1)

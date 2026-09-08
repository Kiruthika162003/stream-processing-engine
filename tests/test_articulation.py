from __future__ import annotations

import random

import pytest

from rill.articulation import articulation_points
from rill.errors import Invalid


def _components(graph, removed):
    seen = set()
    comp = 0
    for s in graph:
        if s == removed or s in seen:
            continue
        comp += 1
        stack = [s]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            for y in graph.get(x, []):
                if y != removed and y not in seen:
                    stack.append(y)
    return comp


def _brute(graph):
    base = _components(graph, None)
    return {v for v in graph if _components(graph, v) > base}


class TestKnownGraphs:
    def test_a_path_cuts_at_its_interior(self):
        path = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2]}
        assert articulation_points(path) == {1, 2}

    def test_a_star_cuts_at_its_center(self):
        star = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}
        assert articulation_points(star) == {0}

    def test_a_cycle_has_no_cut_vertices(self):
        tri = {0: [1, 2], 1: [0, 2], 2: [0, 1]}
        assert articulation_points(tri) == set()


class TestAgainstBrute:
    def test_it_matches_removing_each_vertex(self):
        def rand_graph(rng, n):
            g = {i: [] for i in range(n)}
            for i in range(n):
                for j in range(i + 1, n):
                    if rng.random() < 0.25:
                        g[i].append(j)
                        g[j].append(i)
            return g

        rng = random.Random(53)
        for _ in range(3000):
            n = rng.randint(1, 10)
            g = rand_graph(rng, n)
            assert articulation_points(g) == _brute(g)


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            articulation_points(None)

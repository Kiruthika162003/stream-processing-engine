from __future__ import annotations

import random
from collections import Counter

import pytest

from rill.errors import Invalid
from rill.hierholzer import eulerian_trail


def _valid_trail(edges, trail):
    if len(trail) != len(edges) + 1:
        return False
    used = Counter((trail[i], trail[i + 1]) for i in range(len(trail) - 1))
    return used == Counter(edges)


class TestTrail:
    def test_a_circuit(self):
        edges = [(0, 1), (1, 2), (2, 0)]
        trail = eulerian_trail(edges)
        assert trail[0] == trail[-1]
        assert _valid_trail(edges, trail)

    def test_a_path(self):
        edges = [(0, 1), (1, 2), (2, 3)]
        assert eulerian_trail(edges) == [0, 1, 2, 3]

    def test_empty(self):
        assert eulerian_trail([]) == []

    def test_every_edge_used_exactly_once_on_random_eulerian_graphs(self):
        rng = random.Random(79)
        tested = 0
        for _ in range(3000):
            n = rng.randint(2, 6)
            length = rng.randint(2, 15)
            seq = [rng.randint(0, n - 1) for _ in range(length)]
            seq.append(seq[0])  # close the walk so a trail exists
            edges = [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
            try:
                trail = eulerian_trail(edges)
            except Invalid:
                continue
            tested += 1
            assert _valid_trail(edges, trail)
        assert tested > 1000


class TestRefusals:
    def test_an_unbalanced_graph_is_refused(self):
        with pytest.raises(Invalid):
            eulerian_trail([(0, 1), (0, 2)])

    def test_a_disconnected_graph_is_refused(self):
        with pytest.raises(Invalid):
            eulerian_trail([(0, 1), (1, 0), (2, 3), (3, 2)])

    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            eulerian_trail(None)

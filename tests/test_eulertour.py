from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.eulertour import EulerTour


def _build_random_tree(rng, n):
    children = {0: []}
    for v in range(1, n):
        p = rng.randint(0, v - 1)
        children.setdefault(p, []).append(v)
        children.setdefault(v, [])
    return children


def _reachable(children, u):
    seen = set()
    stack = [u]
    while stack:
        x = stack.pop()
        seen.add(x)
        stack.extend(children.get(x, []))
    return seen


class TestKnownTree:
    def test_entry_and_exit_bracket_the_subtree(self):
        children = {0: [1, 2], 1: [3, 4], 2: [], 3: [], 4: []}
        tour = EulerTour(children, 0)
        assert tour.is_ancestor(0, 3)
        assert not tour.is_ancestor(1, 2)
        assert tour.subtree_size(1) == 3
        assert tour.subtree_size(0) == 5

    def test_a_node_is_its_own_ancestor(self):
        tour = EulerTour({0: [1], 1: []}, 0)
        assert tour.is_ancestor(1, 1)


class TestAgainstReachability:
    def test_ancestor_matches_a_reachability_walk(self):
        rng = random.Random(43)
        for _ in range(2000):
            n = rng.randint(1, 25)
            children = _build_random_tree(rng, n)
            tour = EulerTour(children, 0)
            for u in range(n):
                descendants = _reachable(children, u)
                for v in range(n):
                    assert tour.is_ancestor(u, v) == (v in descendants)
                assert tour.subtree_size(u) == len(descendants)


class TestRefusals:
    def test_none_children_is_refused(self):
        with pytest.raises(Invalid):
            EulerTour(None, 0)

    def test_an_unknown_node_is_refused(self):
        tour = EulerTour({0: []}, 0)
        with pytest.raises(Invalid):
            tour.is_ancestor(0, 9)

    def test_an_unknown_subtree_is_refused(self):
        tour = EulerTour({0: []}, 0)
        with pytest.raises(Invalid):
            tour.subtree_size(9)

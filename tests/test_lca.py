from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.lca import LcaQuery

TREE = {"root": None, "a": "root", "b": "root", "c": "a", "d": "a", "e": "b"}


def _naive(parent: dict[str, str | None], u: str, v: str) -> str:
    ancestors = set()
    node: str | None = u
    while node is not None:
        ancestors.add(node)
        node = parent[node]
    node = v
    while node not in ancestors:
        node = parent[node]
    return node


class TestLca:
    def test_siblings_share_their_parent(self):
        assert LcaQuery(TREE).lca("c", "d") == "a"

    def test_distant_branches_share_the_root(self):
        assert LcaQuery(TREE).lca("c", "e") == "root"

    def test_a_node_and_its_ancestor(self):
        assert LcaQuery(TREE).lca("c", "a") == "a"

    def test_a_node_with_itself(self):
        assert LcaQuery(TREE).lca("c", "c") == "c"

    def test_it_matches_a_naive_path_comparison(self):
        rng = random.Random(4)
        for _ in range(200):
            size = rng.randint(1, 15)
            parent: dict[str, str | None] = {"0": None}
            for i in range(1, size):
                parent[str(i)] = str(rng.randint(0, i - 1))
            query = LcaQuery(parent)
            for u in parent:
                for v in parent:
                    assert query.lca(u, v) == _naive(parent, u, v)


class TestRefusals:
    def test_multiple_roots_are_refused(self):
        with pytest.raises(Invalid):
            LcaQuery({"a": None, "b": None})

    def test_an_unknown_node_is_refused(self):
        with pytest.raises(Invalid):
            LcaQuery(TREE).lca("c", "ghost")

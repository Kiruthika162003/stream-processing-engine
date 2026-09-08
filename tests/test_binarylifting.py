from __future__ import annotations

import random

import pytest

from rill.binarylifting import AncestorQuery
from rill.errors import Invalid


def _naive(parent: dict[str, str | None], node: str, k: int) -> str | None:
    current: str | None = node
    for _ in range(k):
        current = parent[current]
        if current is None:
            return None
    return current


class TestAncestors:
    def test_a_chain(self):
        parent = {"root": None, "a": "root", "b": "a", "c": "b", "d": "c"}
        query = AncestorQuery(parent)
        assert query.kth_ancestor("d", 1) == "c"
        assert query.kth_ancestor("d", 3) == "a"
        assert query.kth_ancestor("d", 4) == "root"

    def test_zero_is_the_node_itself(self):
        query = AncestorQuery({"root": None, "a": "root"})
        assert query.kth_ancestor("a", 0) == "a"

    def test_running_off_the_top_returns_nothing(self):
        query = AncestorQuery({"root": None, "a": "root"})
        assert query.kth_ancestor("a", 5) is None

    def test_it_matches_a_naive_walk_over_random_trees(self):
        rng = random.Random(3)
        for _ in range(200):
            size = rng.randint(1, 15)
            parent: dict[str, str | None] = {"0": None}
            for i in range(1, size):
                parent[str(i)] = str(rng.randint(0, i - 1))
            query = AncestorQuery(parent)
            for node in parent:
                for k in range(size + 2):
                    assert query.kth_ancestor(node, k) == _naive(parent, node, k)


class TestRefusals:
    def test_an_unknown_node_is_refused(self):
        with pytest.raises(Invalid):
            AncestorQuery({"root": None}).kth_ancestor("ghost", 1)

    def test_a_negative_k_is_refused(self):
        with pytest.raises(Invalid):
            AncestorQuery({"root": None}).kth_ancestor("root", -1)

    def test_no_nodes_is_refused(self):
        with pytest.raises(Invalid):
            AncestorQuery({})

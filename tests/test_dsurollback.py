from __future__ import annotations

import random

import pytest

from rill.dsurollback import RollbackDSU
from rill.errors import Invalid


def _ref_connected(n, unions):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for a, b in unions:
        parent[find(a)] = find(b)
    return [[find(i) == find(j) for j in range(n)] for i in range(n)]


class TestRollback:
    def test_a_union_then_undo_restores_connectivity(self):
        dsu = RollbackDSU(5)
        dsu.union(0, 1)
        dsu.union(2, 3)
        snap = dsu.snapshot()
        dsu.union(1, 3)
        assert dsu.connected(0, 3)
        dsu.rollback_to(snap)
        assert not dsu.connected(0, 3)
        assert dsu.connected(0, 1)  # the earlier union survives

    def test_a_redundant_union_is_a_reversible_noop(self):
        dsu = RollbackDSU(3)
        dsu.union(0, 1)
        assert dsu.union(0, 1) is False  # already joined
        dsu.rollback()  # undoing the noop leaves 0 and 1 joined
        assert dsu.connected(0, 1)

    def test_random_union_and_undo_match_a_recomputation(self):
        rng = random.Random(83)
        for _ in range(2000):
            n = rng.randint(1, 8)
            dsu = RollbackDSU(n)
            active = []
            for _ in range(rng.randint(1, 30)):
                if active and rng.random() < 0.4:
                    dsu.rollback()
                    active.pop()
                else:
                    a, b = rng.randint(0, n - 1), rng.randint(0, n - 1)
                    dsu.union(a, b)
                    active.append((a, b))
            ref = _ref_connected(n, active)
            for i in range(n):
                for j in range(n):
                    assert dsu.connected(i, j) == ref[i][j]


class TestRefusals:
    def test_a_negative_size_is_refused(self):
        with pytest.raises(Invalid):
            RollbackDSU(-1)

    def test_rolling_back_nothing_is_refused(self):
        with pytest.raises(Invalid):
            RollbackDSU(3).rollback()

    def test_an_out_of_range_node_is_refused(self):
        with pytest.raises(Invalid):
            RollbackDSU(3).find(9)

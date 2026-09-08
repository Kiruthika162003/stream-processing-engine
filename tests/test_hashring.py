from __future__ import annotations

from collections import Counter

import pytest

from rill.errors import Invalid
from rill.hashring import HashRing

KEYS = [f"key-{number}" for number in range(3000)]


class TestRouting:
    def test_a_key_routes_to_a_stable_owner(self):
        ring = HashRing(vnodes=50)
        for node in ("a", "b", "c"):
            ring.add(node)
        first = ring.owner("key-1")
        assert first in {"a", "b", "c"}
        assert ring.owner("key-1") == first


class TestSmallMovement:
    def test_adding_a_node_moves_about_one_in_n_keys(self):
        ring = HashRing(vnodes=100)
        for node in ("a", "b", "c", "d"):
            ring.add(node)
        before = {key: ring.owner(key) for key in KEYS}
        ring.add("e")
        after = {key: ring.owner(key) for key in KEYS}
        moved = sum(1 for key in KEYS if before[key] != after[key])
        # ideal for the fifth node is one in five; modulo would move
        # closer to four in five.
        assert 0.15 < moved / len(KEYS) < 0.25


class TestVirtualNodesBalance:
    def test_one_point_per_node_is_lopsided(self):
        ring = HashRing(vnodes=1)
        for node in ("a", "b", "c", "d", "e"):
            ring.add(node)
        loads = Counter(ring.owner(key) for key in KEYS)
        counts = [loads[node] for node in ring.nodes()]
        assert max(counts) / (sum(counts) / len(counts)) > 1.8

    def test_many_points_per_node_evens_the_load(self):
        ring = HashRing(vnodes=200)
        for node in ("a", "b", "c", "d", "e"):
            ring.add(node)
        loads = Counter(ring.owner(key) for key in KEYS)
        counts = [loads[node] for node in ring.nodes()]
        assert max(counts) / (sum(counts) / len(counts)) < 1.2


class TestRemoval:
    def test_removing_a_node_drops_it_from_the_ring(self):
        ring = HashRing(vnodes=50)
        for node in ("a", "b", "c"):
            ring.add(node)
        ring.remove("b")
        assert ring.nodes() == ["a", "c"]
        assert ring.owner("key-1") in {"a", "c"}


class TestRefusals:
    def test_a_nonpositive_vnode_count_is_refused(self):
        with pytest.raises(Invalid):
            HashRing(vnodes=0)

    def test_owner_on_an_empty_ring_is_refused(self):
        with pytest.raises(Invalid):
            HashRing(vnodes=1).owner("key")

    def test_removing_an_absent_node_is_refused(self):
        ring = HashRing(vnodes=1)
        ring.add("a")
        with pytest.raises(Invalid):
            ring.remove("z")

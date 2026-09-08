from __future__ import annotations

from collections import Counter

import pytest

from rill.errors import Invalid
from rill.rendezvous import RendezvousHash

KEYS = [f"key-{number}" for number in range(3000)]


def _five() -> RendezvousHash:
    ring = RendezvousHash()
    for node in ("a", "b", "c", "d", "e"):
        ring.add(node)
    return ring


class TestBalance:
    def test_load_is_even_with_no_virtual_nodes(self):
        ring = _five()
        loads = Counter(ring.owner(key) for key in KEYS)
        counts = [loads[node] for node in ring.nodes()]
        assert max(counts) / (sum(counts) / len(counts)) < 1.1


class TestMinimalDisruption:
    def test_removing_a_node_moves_only_its_own_keys(self):
        ring = _five()
        before = {key: ring.owner(key) for key in KEYS}
        owned_by_e = sum(1 for key in KEYS if before[key] == "e")
        ring.remove("e")
        moved = sum(1 for key in KEYS if before[key] != ring.owner(key))
        assert moved == owned_by_e

    def test_a_key_routes_to_a_stable_owner(self):
        ring = _five()
        first = ring.owner("key-42")
        assert ring.owner("key-42") == first


class TestReplicas:
    def test_replicas_returns_the_top_k_distinct_nodes(self):
        ring = _five()
        replicas = ring.replicas("key-1", 3)
        assert len(replicas) == 3
        assert len(set(replicas)) == 3
        assert replicas[0] == ring.owner("key-1")


class TestRefusals:
    def test_routing_with_no_nodes_is_refused(self):
        with pytest.raises(Invalid):
            RendezvousHash().owner("key")

    def test_removing_an_absent_node_is_refused(self):
        with pytest.raises(Invalid):
            _five().remove("z")

    def test_a_nonpositive_replica_count_is_refused(self):
        with pytest.raises(Invalid):
            _five().replicas("key", 0)

"""Rendezvous hashing: every key picks its node by a score, no ring and no virtual nodes.

Consistent hashing needs virtual nodes to spread load evenly,
because a ring with one point per node has wildly uneven arcs.
Rendezvous hashing reaches the same two goals, even distribution
and minimal disruption on a membership change, by a different
route that needs no tuning. For a key, every node computes a
score by hashing the pair of node and key, and the key belongs to
the node with the highest score. Distribution is even because the
scores are uniform and independent, so each node wins about its
fair share of keys with no virtual points to configure, and
disruption is minimal because adding a node only steals the keys
for which its score is now the highest and removing one only
hands off the keys it used to win, while every other key keeps
the node it had. Ranking the scores also gives the top-k nodes
for free, which is exactly the replica set for a key. The cost is
that a lookup scores every node, O(n) against the ring's
logarithmic search, so rendezvous wins on small clusters and
simplicity and the ring wins on large ones. This module scores,
routes, and ranks replicas, so the even split and the small
movement are measurements, not claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_digest
from rill.errors import Invalid


def _score(node: str, key: str) -> int:
    return int(stable_digest(f"{node}:{key}")[:8], 16)


@dataclass
class RendezvousHash:
    _nodes: set[str] = field(default_factory=set)

    def add(self, node: str) -> None:
        self._nodes.add(node)

    def remove(self, node: str) -> None:
        if node not in self._nodes:
            raise Invalid(f"{node} is not a member")
        self._nodes.discard(node)

    def owner(self, key: str) -> str:
        if not self._nodes:
            raise Invalid("no nodes to route to")
        return max(self._nodes, key=lambda node: _score(node, key))

    def replicas(self, key: str, count: int) -> list[str]:
        if count < 1:
            raise Invalid("count must be positive")
        ranked = sorted(
            self._nodes, key=lambda node: _score(node, key), reverse=True
        )
        return ranked[:count]

    def nodes(self) -> list[str]:
        return sorted(self._nodes)

"""Consistent hashing: adding a node moves a slice of keys, not almost all of them.

Routing keys to nodes by hash modulo the node count is fine
until the count changes, and then it is a disaster: add one node
and the modulus changes for every key, so nearly every key
re-homes at once and the whole cache or state store is cold in a
single step. A hash ring fixes the re-homing. Nodes and keys both
hash onto a ring, a key belongs to the first node clockwise from
it, and adding a node steals only the keys in the arc between it
and the node before it, so roughly one in N keys move rather than
all of them. The catch is balance: with one point per node the
arcs are wildly uneven and one unlucky node owns a huge span,
which is why each node is placed at many virtual points, so its
ownership is scattered into many small arcs whose sizes average
out and the load evens. This module builds the ring, routes keys,
and adds and removes nodes, so both properties, the small key
movement on a change and the smoothing that virtual nodes buy,
are measurements a test can hold rather than folklore.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field

from rill.content_hash import stable_digest
from rill.errors import Invalid


def _position(text: str) -> int:
    return int(stable_digest(text)[:8], 16)


@dataclass
class HashRing:
    vnodes: int
    _positions: list[int] = field(default_factory=list)
    _owner: dict[int, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.vnodes <= 0:
            raise Invalid("need at least one virtual node per node")

    def add(self, node: str) -> None:
        for replica in range(self.vnodes):
            point = _position(f"{node}#{replica}")
            if point in self._owner:
                continue
            bisect.insort(self._positions, point)
            self._owner[point] = node

    def remove(self, node: str) -> None:
        if node not in set(self._owner.values()):
            raise Invalid(f"{node} is not on the ring")
        survivors = [p for p in self._positions if self._owner[p] != node]
        self._positions = survivors
        self._owner = {p: n for p, n in self._owner.items() if n != node}

    def owner(self, key: str) -> str:
        if not self._positions:
            raise Invalid("the ring is empty")
        point = _position(key)
        index = bisect.bisect_left(self._positions, point)
        if index == len(self._positions):
            index = 0
        return self._owner[self._positions[index]]

    def nodes(self) -> list[str]:
        return sorted(set(self._owner.values()))

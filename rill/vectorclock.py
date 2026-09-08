"""Vector clocks: telling a causal order from a coincidence the scalar clock cannot.

A single counter per event gives a total order and lies about
what it means: if event A has a smaller Lamport timestamp than B
it may have caused B or the two may have happened on different
nodes with no relationship at all, and the scalar cannot tell the
two apart. A vector clock carries one counter per node. A node
bumps its own entry on a local event, stamps outgoing messages
with its whole vector, and on receiving one takes the elementwise
maximum before bumping its own entry again, so the vector records
everything that causally precedes an event and nothing that does
not. Now the comparison is honest: A happens before B when every
entry of A is at most B's and at least one is strictly less, B
happens before A in the mirror case, and when neither dominates
the events are concurrent, which is precisely the verdict the
scalar clock erases. That verdict is what conflict detection in
replicated state runs on, because two concurrent writes are a
conflict to resolve while two ordered writes are a history to
keep. This module keeps a node's vector, merges on receive, and
classifies any two vectors as before, after, equal, or
concurrent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

BEFORE = "before"
AFTER = "after"
EQUAL = "equal"
CONCURRENT = "concurrent"


@dataclass
class VectorClock:
    node: str
    _clock: dict[str, int] = field(default_factory=dict)

    def tick(self) -> dict[str, int]:
        self._clock[self.node] = self._clock.get(self.node, 0) + 1
        return self.vector()

    def receive(self, incoming: dict[str, int]) -> dict[str, int]:
        for node, count in incoming.items():
            self._clock[node] = max(self._clock.get(node, 0), count)
        return self.tick()

    def vector(self) -> dict[str, int]:
        return dict(self._clock)


def _dominates(left: dict[str, int], right: dict[str, int]) -> bool:
    nodes = set(left) | set(right)
    ge = all(left.get(n, 0) >= right.get(n, 0) for n in nodes)
    gt = any(left.get(n, 0) > right.get(n, 0) for n in nodes)
    return ge and gt


def compare(left: dict[str, int], right: dict[str, int]) -> str:
    if left == {} and right == {}:
        raise Invalid("cannot compare two empty vectors")
    if left == right:
        return EQUAL
    if _dominates(right, left):
        return BEFORE
    if _dominates(left, right):
        return AFTER
    return CONCURRENT

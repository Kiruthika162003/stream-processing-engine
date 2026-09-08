"""CRDT counters: merging concurrent increments by keeping each replica's own tally.

Two replicas that both increment a shared counter while
partitioned cannot be reconciled by last-write-wins, because
last-write-wins keeps one replica's value and throws the other's
increments away, so a counter that went up by three on one side
and five on the other comes back as five, silently losing three.
A grow-only CRDT counter avoids the loss by never storing a
single number. Each replica keeps its own per-node tally and only
ever adds to its own entry, the merge of two replicas takes the
elementwise maximum of their tallies, and the counter's value is
the sum across all entries, so the three and the five both
survive the merge and the value is eight. The merge is
commutative, associative, and idempotent, which is what lets
replicas exchange state in any order, any number of times, and
still converge. A PN-counter pairs two grow-only counters, one
for increments and one for decrements, to allow going down as
well as up without breaking the same guarantee. This module
holds both and merges them, so the concurrent-increment case
that defeats a scalar is a passing test.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class GCounter:
    node: str
    _counts: dict[str, int] = field(default_factory=dict)

    def increment(self, by: int = 1) -> None:
        if by < 0:
            raise Invalid("a grow-only counter cannot decrease; use a PN-counter")
        self._counts[self.node] = self._counts.get(self.node, 0) + by

    def value(self) -> int:
        return sum(self._counts.values())

    def merge(self, other: GCounter) -> None:
        for node, count in other._counts.items():
            self._counts[node] = max(self._counts.get(node, 0), count)

    def state(self) -> dict[str, int]:
        return dict(self._counts)


@dataclass
class PNCounter:
    node: str
    _plus: GCounter = field(init=False)
    _minus: GCounter = field(init=False)

    def __post_init__(self) -> None:
        self._plus = GCounter(self.node)
        self._minus = GCounter(self.node)

    def increment(self, by: int = 1) -> None:
        self._plus.increment(by)

    def decrement(self, by: int = 1) -> None:
        self._minus.increment(by)

    def value(self) -> int:
        return self._plus.value() - self._minus.value()

    def merge(self, other: PNCounter) -> None:
        self._plus.merge(other._plus)
        self._minus.merge(other._minus)

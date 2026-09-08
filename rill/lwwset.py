"""LWW-element-set: a replicated set that resolves add against remove by timestamp.

The OR-set resolves a concurrent add and remove by tags and causal
observation; the last-writer-wins element set resolves them more
simply, by time. It keeps, per element, the latest timestamp at
which it was added and the latest at which it was removed, and the
element is present when its add timestamp is at least its remove
timestamp. So a remove stamped later than the last add wins and
the element is gone, an add stamped later than the last remove wins
and it is present, and the tie, equal timestamps, is broken by a
fixed bias, here add-wins so an element is present when the stamps
are equal. Merging two replicas takes the elementwise maximum of
both the add and the remove timestamps, which is commutative,
associative, and idempotent, so replicas converge. The trade
against the OR-set is that this scheme trusts timestamps to order
events, which is fine with well-synchronized clocks or logical
timestamps and wrong if a laggy clock stamps a stale remove after
a real add, whereas the OR-set needs no clock at all. It is
simpler and cheaper when a timestamp is available and the tie bias
is acceptable. This module keeps the two timestamp maps, resolves
membership by comparison, and merges by maximum, so the
time-ordered add-versus-remove resolution is a checkable outcome.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class LwwSet:
    _added: dict[str, int] = field(default_factory=dict)
    _removed: dict[str, int] = field(default_factory=dict)

    def add(self, element: str, timestamp: int) -> None:
        if timestamp < 0:
            raise Invalid("timestamp cannot be negative")
        self._added[element] = max(self._added.get(element, -1), timestamp)

    def remove(self, element: str, timestamp: int) -> None:
        if timestamp < 0:
            raise Invalid("timestamp cannot be negative")
        self._removed[element] = max(self._removed.get(element, -1), timestamp)

    def contains(self, element: str) -> bool:
        if element not in self._added:
            return False
        return self._added[element] >= self._removed.get(element, -1)

    def elements(self) -> set[str]:
        return {element for element in self._added if self.contains(element)}

    def merge(self, other: LwwSet) -> None:
        for element, timestamp in other._added.items():
            self._added[element] = max(self._added.get(element, -1), timestamp)
        for element, timestamp in other._removed.items():
            self._removed[element] = max(self._removed.get(element, -1), timestamp)

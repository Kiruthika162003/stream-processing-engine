"""Grow-only and two-phase sets: mergeable sets, and the removal you cannot take back.

Beyond the add-wins OR-set are two simpler set CRDTs whose
constraints are the point. The grow-only set only ever adds:
merge is set union, which is commutative, associative, and
idempotent, so replicas converge trivially, but nothing can ever
be removed, which is exactly right for an append-only membership,
a set of seen ids, a collection that only accumulates. The
two-phase set adds removal by pairing the add-set with a tombstone
set of removed elements, and an element is present when it has
been added and not tombstoned. The constraint that makes it a
clean CRDT is severe: once an element is tombstoned it can never
be re-added, because a later add would have to un-tombstone it and
there is no monotonic way for two replicas to agree on that. So a
two-phase set is remove-wins and permanent, the mirror image of
the OR-set's add-wins re-addable behavior, and choosing between
them is choosing whether a removed element is gone for good or may
return. Both merge by unioning their underlying sets, so
convergence is free, and the difference is entirely in what the
constraints allow. This module implements both and their merges,
so the permanence of a two-phase removal, and its contrast with
the OR-set, are a passing test rather than a footnote about set
CRDTs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class GSet:
    _elements: set[str] = field(default_factory=set)

    def add(self, element: str) -> None:
        self._elements.add(element)

    def contains(self, element: str) -> bool:
        return element in self._elements

    def merge(self, other: GSet) -> None:
        self._elements |= other._elements

    def elements(self) -> set[str]:
        return set(self._elements)


@dataclass
class TwoPhaseSet:
    _added: set[str] = field(default_factory=set)
    _removed: set[str] = field(default_factory=set)

    def add(self, element: str) -> None:
        if element in self._removed:
            raise Invalid(f"{element} was removed; a two-phase set cannot re-add it")
        self._added.add(element)

    def remove(self, element: str) -> None:
        if element not in self._added:
            raise Invalid(f"{element} was never added")
        self._removed.add(element)

    def contains(self, element: str) -> bool:
        return element in self._added and element not in self._removed

    def merge(self, other: TwoPhaseSet) -> None:
        self._added |= other._added
        self._removed |= other._removed

    def elements(self) -> set[str]:
        return self._added - self._removed

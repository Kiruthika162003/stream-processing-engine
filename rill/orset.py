"""OR-Set: a replicated set where a concurrent add survives a remove it never saw.

A set that replicates add and remove naively has no answer for
the case that matters: one replica removes an element while
another, partitioned, adds it, and on merge the element is both
present and absent with nothing to break the tie. The observed-
remove set breaks it by tagging. Every add stamps the element
with a unique tag, and a remove does not delete the element, it
tombstones exactly the tags it has currently observed. An element
is in the set when it carries at least one add tag that no
tombstone covers. Now the concurrent case resolves cleanly: the
remove on one replica tombstones the tags it saw, the add on the
other replica minted a fresh tag that remove never saw, and after
the merge that fresh tag is uncovered, so the element is present.
The rule this produces is add-wins, a concurrent add beats a
concurrent remove, which is the intuitive outcome and, more to
the point, a deterministic one both replicas reach. This module
keeps the add tags and the tombstones, merges by unioning both,
and reports membership as an uncovered tag, so the add-wins
convergence is a test and not a hope.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class ORSet:
    _adds: dict[str, set[str]] = field(default_factory=dict)
    _removes: dict[str, set[str]] = field(default_factory=dict)

    def add(self, element: str, tag: str) -> None:
        if not tag:
            raise Invalid("every add needs a unique tag")
        self._adds.setdefault(element, set()).add(tag)

    def remove(self, element: str) -> None:
        observed = self._adds.get(element, set())
        if observed:
            self._removes.setdefault(element, set()).update(observed)

    def contains(self, element: str) -> bool:
        live = self._adds.get(element, set()) - self._removes.get(element, set())
        return bool(live)

    def elements(self) -> list[str]:
        return sorted(e for e in self._adds if self.contains(e))

    def merge(self, other: ORSet) -> None:
        for element, tags in other._adds.items():
            self._adds.setdefault(element, set()).update(tags)
        for element, tags in other._removes.items():
            self._removes.setdefault(element, set()).update(tags)

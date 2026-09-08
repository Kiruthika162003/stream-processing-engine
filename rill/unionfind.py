"""Union-Find: merging overlapping sessions into components, fast only with compression.

Session windows are connected components: two events belong to
the same session if a chain of overlaps links them, and merging
them as events arrive is exactly the disjoint-set problem. Each
element points toward a representative, union links two
representatives, and find walks parent pointers to the root that
names an element's component. Done naively the find walk is the
whole cost, because unions can build a long chain and every find
then walks its full length, so a run of merges degrades to
quadratic. Two cheap disciplines fix it. Union by rank always
hangs the shorter tree under the taller so the trees stay bushy
rather than stringy, and path compression points every node the
find touched straight at the root on the way back, so the second
find on the same element is a single hop. Together they make find
and union effectively constant, which is why a session merger can
keep up with the stream. This module implements both, and can
disable compression on request, so the difference between a find
that walks a chain and one that has been flattened is a measured
path length rather than a claim about inverse-Ackermann.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class UnionFind:
    compress: bool = True
    _parent: dict[str, str] = field(default_factory=dict)
    _rank: dict[str, int] = field(default_factory=dict)
    _last_walk: int = 0

    def add(self, element: str) -> None:
        if element not in self._parent:
            self._parent[element] = element
            self._rank[element] = 0

    def find(self, element: str) -> str:
        if element not in self._parent:
            raise Invalid(f"unknown element {element}")
        self._last_walk = 0
        root = element
        while self._parent[root] != root:
            root = self._parent[root]
            self._last_walk += 1
        if self.compress:
            node = element
            while self._parent[node] != root:
                self._parent[node], node = root, self._parent[node]
        return root

    def union(self, left: str, right: str) -> None:
        self.add(left)
        self.add(right)
        lroot, rroot = self.find(left), self.find(right)
        if lroot == rroot:
            return
        if self._rank[lroot] < self._rank[rroot]:
            lroot, rroot = rroot, lroot
        self._parent[rroot] = lroot
        if self._rank[lroot] == self._rank[rroot]:
            self._rank[lroot] += 1

    def connected(self, left: str, right: str) -> bool:
        return self.find(left) == self.find(right)

    def components(self) -> int:
        return sum(1 for e in self._parent if self.find(e) == e)

    def last_walk(self) -> int:
        return self._last_walk

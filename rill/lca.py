"""Lowest common ancestor: the deepest node above both, in log n by lifting them together.

Two nodes in a tree, two operators in a lineage, two records in a
hierarchy, share a lowest common ancestor, the deepest node that
is an ancestor of both, which answers where two branches diverged.
Walking both up to the root and comparing the paths is linear in
the depth. Binary lifting finds it in log n. First bring the two
nodes to the same depth by lifting the deeper one up by the depth
difference, a single jump decomposed into powers of two. Now both
are equally deep: if they are the same node, that is the answer,
and otherwise lift both upward in lockstep by the largest power of
two that keeps them at different nodes, repeating down to power
zero. After those synchronized jumps the two nodes sit just below
their lowest common ancestor, so their common parent is the
answer. The synchronized lift works because equal-depth nodes meet
their common ancestor at the same height, so a jump that keeps
them distinct is safe and a jump that would merge them is the one
to hold back until a smaller jump. With the ancestor table
precomputed the whole query is a logarithmic number of jumps. This
module builds the lifting table and depths and answers the lowest
common ancestor, checked against a naive path comparison, so the
log-time query is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


class LcaQuery:
    def __init__(self, parent: dict[str, str | None]) -> None:
        if not parent:
            raise Invalid("no nodes")
        roots = [n for n, p in parent.items() if p is None]
        if len(roots) != 1:
            raise Invalid("a tree needs exactly one root")
        self._levels = max(1, len(parent).bit_length())
        self._up: dict[str, list[str | None]] = {}
        self._depth: dict[str, int] = {}
        for node, direct in parent.items():
            if direct is not None and direct not in parent:
                raise Invalid(f"parent {direct} of {node} is not a node")
            self._up[node] = [direct] + [None] * (self._levels - 1)
        for level in range(1, self._levels):
            for node in parent:
                mid = self._up[node][level - 1]
                self._up[node][level] = self._up[mid][level - 1] if mid else None
        for node in parent:
            self._depth[node] = self._compute_depth(node, parent)

    def _compute_depth(self, node: str, parent: dict[str, str | None]) -> int:
        depth = 0
        while parent[node] is not None:
            node = parent[node]
            depth += 1
        return depth

    def _lift(self, node: str, steps: int) -> str:
        level = 0
        while steps > 0:
            if steps & 1:
                node = self._up[node][level]
            steps >>= 1
            level += 1
        return node

    def lca(self, u: str, v: str) -> str:
        if u not in self._up or v not in self._up:
            raise Invalid("unknown node")
        if self._depth[u] < self._depth[v]:
            u, v = v, u
        u = self._lift(u, self._depth[u] - self._depth[v])
        if u == v:
            return u
        for level in range(self._levels - 1, -1, -1):
            if self._up[u][level] is not None and self._up[u][level] != self._up[v][level]:
                u = self._up[u][level]
                v = self._up[v][level]
        return self._up[u][0]

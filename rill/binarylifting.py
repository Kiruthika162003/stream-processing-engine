"""Binary lifting: the kth ancestor of a node in log k, by jumping in powers of two.

Tracing lineage up an operator tree or a dependency hierarchy asks
for the kth ancestor of a node, the operator k stages upstream, and
walking k parent pointers is O(k), slow when k is large and the
query is hot. Binary lifting precomputes ancestor jumps at every
power of two. For each node it stores its immediate parent, its
grandparent two up, its ancestor four up, eight up, and so on, each
level built from the one below by jumping twice: the ancestor
two-to-the-j up is the ancestor two-to-the-(j minus one) up of the
ancestor two-to-the-(j minus one) up. With that table, any kth
ancestor is reached by decomposing k into its binary ones and
taking the corresponding power-of-two jumps in sequence, so a jump
of thirteen is a jump of eight then four then one, three hops
instead of thirteen. The preprocessing is n log n in space and
time, and each query is log k, which pays off the moment ancestor
queries outnumber a handful. Running off the top of the tree
returns nothing, so a k larger than the node's depth is a clean
absence rather than an error. This module builds the jump table
and answers the kth ancestor, checked against a naive parent walk,
so the log-not-linear query is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


class AncestorQuery:
    def __init__(self, parent: dict[str, str | None]) -> None:
        if not parent:
            raise Invalid("no nodes")
        self._nodes = list(parent)
        max_level = max(1, len(parent).bit_length())
        self._up: dict[str, list[str | None]] = {}
        for node, direct in parent.items():
            if direct is not None and direct not in parent:
                raise Invalid(f"parent {direct} of {node} is not a node")
            self._up[node] = [direct] + [None] * (max_level - 1)
        for level in range(1, max_level):
            for node in self._nodes:
                midway = self._up[node][level - 1]
                self._up[node][level] = (
                    self._up[midway][level - 1] if midway is not None else None
                )
        self._levels = max_level

    def kth_ancestor(self, node: str, k: int) -> str | None:
        if node not in self._up:
            raise Invalid(f"unknown node {node}")
        if k < 0:
            raise Invalid("k cannot be negative")
        current: str | None = node
        level = 0
        while k > 0 and current is not None:
            if k & 1:
                if level >= self._levels:
                    return None
                current = self._up[current][level]
            k >>= 1
            level += 1
        return current

"""Euler tour: flatten a tree so every subtree becomes a contiguous range.

Many questions about a tree are really questions about subtrees: the
sum of values in a node's subtree, whether one node is an ancestor
of another, how many descendants a node has. Answered by walking the
subtree each time they are asked, they cost the subtree's size per
query. The Euler tour turns them into range questions on a flat
array, which range data structures then answer in log time or less.
A depth-first walk stamps each node with an entry time when it is
first reached and an exit time when its whole subtree has been
finished. The key property this produces is that a node's subtree
occupies exactly the contiguous span of entry times from the node's
own entry to its exit, no gaps and nothing foreign, because the walk
does not leave the subtree until every descendant is entered. Two
consequences follow directly. First, node u is an ancestor of node v
exactly when u's entry is at or before v's entry and u's exit is at
or after v's, a pair of comparisons replacing a walk up the tree.
Second, laying the node values out by entry time makes any subtree a
range, so a prefix-sum or a Fenwick tree over that layout gives
subtree sums. The finding worth stating is that the entry-to-exit
span being exactly the subtree, with no interleaving, is what makes
the flattening lossless for subtree queries. This module computes
entry and exit times over a rooted tree and offers the ancestor test
and subtree size from them, and a test checks the ancestor relation
against a direct reachability walk, so the flattening is confirmed.
"""

from __future__ import annotations

from rill.errors import Invalid


class EulerTour:
    def __init__(self, children: dict[int, list[int]], root: int) -> None:
        if children is None:
            raise Invalid("children map must not be None")
        self.entry: dict[int, int] = {}
        self.exit: dict[int, int] = {}
        clock = 0
        # iterative DFS carrying an "entering" flag to stamp exit on the way up
        stack: list[tuple[int, bool]] = [(root, True)]
        while stack:
            node, entering = stack.pop()
            if entering:
                self.entry[node] = clock
                clock += 1
                stack.append((node, False))
                for child in reversed(children.get(node, [])):
                    stack.append((child, True))
            else:
                self.exit[node] = clock - 1

    def is_ancestor(self, u: int, v: int) -> bool:
        if u not in self.entry or v not in self.entry:
            raise Invalid("both nodes must be in the tree")
        return self.entry[u] <= self.entry[v] and self.exit[v] <= self.exit[u]

    def subtree_size(self, u: int) -> int:
        if u not in self.entry:
            raise Invalid("node must be in the tree")
        return self.exit[u] - self.entry[u] + 1

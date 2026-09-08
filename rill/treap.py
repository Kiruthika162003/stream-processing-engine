"""Treap: a binary search tree kept balanced by random priorities, not rotations rules.

A plain binary search tree degrades to a linked list when keys
arrive sorted, because each new key hangs off the rightmost node and
the height grows linearly. Balanced trees fix this with explicit
rebalancing rules, red-black colors or AVL height bounds, which are
correct but fiddly. A treap reaches the same expected balance with a
much simpler idea: give every key a random priority, and keep the
tree a search tree by key while also keeping it a heap by priority,
every parent's priority above its children's. There is exactly one
shape satisfying both for a given set of key-priority pairs, and it
is the shape you would get by inserting the keys in priority order
into a plain tree. Since the priorities are random, that insertion
order is a random permutation, and a search tree built from a random
permutation has expected height about 1.39 times log n, the same
logarithmic depth a random binary search tree enjoys, with no
adversarial ordering possible because the adversary controls the
keys but not the priorities. Insertion places the key by search-tree
rule at a leaf, then rotates it up while its priority exceeds its
parent's, restoring the heap property, and each rotation preserves
the search-tree order. The distinguishing property is that balance
is probabilistic and rule-free: no case analysis, just a heap
invariant on random numbers. This module builds a treap with insert
and membership, and tests confirm the in-order keys stay sorted, the
heap property holds at every node, and the height stays near log n,
so the randomized balance is demonstrated.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

from rill.errors import Invalid


class _Node:
    __slots__ = ("key", "left", "priority", "right")

    def __init__(self, key: int, priority: float) -> None:
        self.key = key
        self.priority = priority
        self.left: _Node | None = None
        self.right: _Node | None = None


class Treap:
    def __init__(self, priority: Callable[[], float]) -> None:
        if priority is None:
            raise Invalid("a priority source is required")
        self._priority = priority
        self._root: _Node | None = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: int) -> bool:
        node = self._root
        while node is not None:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

    def insert(self, key: int) -> None:
        if key in self:
            return
        self._root = self._insert(self._root, key)
        self._size += 1

    def _insert(self, node: _Node | None, key: int) -> _Node:
        if node is None:
            return _Node(key, self._priority())
        if key < node.key:
            node.left = self._insert(node.left, key)
            if node.left.priority > node.priority:
                node = self._rotate_right(node)
        else:
            node.right = self._insert(node.right, key)
            if node.right.priority > node.priority:
                node = self._rotate_left(node)
        return node

    def _rotate_right(self, node: _Node) -> _Node:
        pivot = node.left
        node.left = pivot.right
        pivot.right = node
        return pivot

    def _rotate_left(self, node: _Node) -> _Node:
        pivot = node.right
        node.right = pivot.left
        pivot.left = node
        return pivot

    def __iter__(self) -> Iterator[int]:
        yield from self._inorder(self._root)

    def _inorder(self, node: _Node | None) -> Iterator[int]:
        if node is not None:
            yield from self._inorder(node.left)
            yield node.key
            yield from self._inorder(node.right)

    def height(self) -> int:
        return self._height(self._root)

    def _height(self, node: _Node | None) -> int:
        if node is None:
            return 0
        return 1 + max(self._height(node.left), self._height(node.right))

    def heap_property_holds(self) -> bool:
        return self._heap_ok(self._root)

    def _heap_ok(self, node: _Node | None) -> bool:
        if node is None:
            return True
        for child in (node.left, node.right):
            if child is not None and child.priority > node.priority:
                return False
        return self._heap_ok(node.left) and self._heap_ok(node.right)

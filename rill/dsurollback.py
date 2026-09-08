"""Union-find with rollback: undo a union by restoring the two slots it touched.

The ordinary union-find is fast partly because of path compression,
which flattens the tree as it answers queries. That flattening is
also why it cannot be undone: a single find rewrites many parent
pointers, so there is no small record to reverse. Some problems,
offline dynamic connectivity chief among them, need exactly that,
the ability to union two sets, do some work, and then roll the
structure back to before the union. The rollback variant gives it up
front by refusing path compression and relying on union by size
alone. Union by size, always hanging the smaller tree under the
larger root, keeps every tree's height logarithmic on its own, so
find stays log-time even without compression. And because a union
now changes exactly two things, the parent of one root and the size
of the other, each union can be logged as that pair of old values and
undone by restoring them. A stack of these logs lets the structure
wind back any number of unions in reverse order, each undo a constant
amount of work. The trade is stated plainly: queries are log-time
rather than the near-constant of the compressed version, and that
slowdown is the price of reversibility, worth paying only when the
problem genuinely needs to undo. The finding worth stating is that
path compression and rollback are mutually exclusive, and union by
size is what keeps the uncompressed structure fast enough to be
useful. This module implements union-find with a rollback stack, and
a test drives random union and undo sequences and checks connectivity
against a from-scratch recomputation, so the undo is confirmed exact.
"""

from __future__ import annotations

from rill.errors import Invalid


class RollbackDSU:
    def __init__(self, size: int) -> None:
        if size < 0:
            raise Invalid("size must not be negative")
        self._parent = list(range(size))
        self._size = [1] * size
        self._history: list[tuple[int, int, int, int]] = []

    def find(self, x: int) -> int:
        if x < 0 or x >= len(self._parent):
            raise Invalid("node is out of range")
        while self._parent[x] != x:
            x = self._parent[x]
        return x

    def connected(self, a: int, b: int) -> bool:
        return self.find(a) == self.find(b)

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            self._history.append((-1, -1, -1, -1))
            return False
        if self._size[ra] < self._size[rb]:
            ra, rb = rb, ra
        # rb hangs under ra; log the two slots we are about to change
        self._history.append((rb, self._parent[rb], ra, self._size[ra]))
        self._parent[rb] = ra
        self._size[ra] += self._size[rb]
        return True

    def rollback(self) -> None:
        if not self._history:
            raise Invalid("nothing to roll back")
        child, old_parent, root, old_size = self._history.pop()
        if child == -1:
            return
        self._parent[child] = old_parent
        self._size[root] = old_size

    def snapshot(self) -> int:
        return len(self._history)

    def rollback_to(self, snapshot: int) -> None:
        if snapshot < 0 or snapshot > len(self._history):
            raise Invalid("snapshot is out of range")
        while len(self._history) > snapshot:
            self.rollback()

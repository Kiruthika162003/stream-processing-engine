"""Skip list: the ordered index memtables use, fast only because the coin is fair.

A skip list keeps keys in order with expected logarithmic search
and insert and no rebalancing, which is why it backs the in-memory
memtables of more than one stream state store. It is a linked list
whose nodes carry extra forward pointers at higher levels, and a
search drops down the levels, skipping far at the top and
narrowing as it descends, so it steps over most of the list
instead of walking it. The whole speed rests on the height
distribution: each inserted node flips a coin to decide how tall
it is, and a fair coin gives a geometric spread of heights whose
express lanes at the top halve the search each level, landing the
cost at log n. Rig the coin and the guarantee evaporates, because
a coin that never promotes builds a list one level tall, a plain
linked list whose search walks every node in O(n), and no amount
of skip-list machinery helps once the levels are gone. This module
takes the coin as an argument so the height distribution is under
the test's control, and it counts the nodes a search visits, so
the log-versus-linear difference between a fair coin and a rigged
one is a number rather than a claim about expectations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class _Node:
    key: int | None
    forward: list[_Node | None]


class SkipList:
    def __init__(self, coin: Callable[[], bool], max_level: int = 16) -> None:
        if max_level < 1:
            raise Invalid("max_level must be positive")
        self.coin = coin
        self.max_level = max_level
        self.level = 1
        self._head = _Node(key=None, forward=[None] * max_level)
        self._visited = 0

    def _random_level(self) -> int:
        level = 1
        while self.coin() and level < self.max_level:
            level += 1
        return level

    def insert(self, key: int) -> None:
        update: list[_Node] = [self._head] * self.max_level
        node = self._head
        for i in range(self.level - 1, -1, -1):
            nxt = node.forward[i]
            while nxt is not None and nxt.key is not None and nxt.key < key:
                node = nxt
                nxt = node.forward[i]
            update[i] = node
        ahead = node.forward[0]
        if ahead is not None and ahead.key == key:
            return
        height = self._random_level()
        if height > self.level:
            for i in range(self.level, height):
                update[i] = self._head
            self.level = height
        fresh = _Node(key=key, forward=[None] * height)
        for i in range(height):
            fresh.forward[i] = update[i].forward[i]
            update[i].forward[i] = fresh

    def contains(self, key: int) -> bool:
        self._visited = 0
        node = self._head
        for i in range(self.level - 1, -1, -1):
            nxt = node.forward[i]
            while nxt is not None and nxt.key is not None and nxt.key < key:
                node = nxt
                self._visited += 1
                nxt = node.forward[i]
        ahead = node.forward[0]
        return ahead is not None and ahead.key == key

    def to_list(self) -> list[int]:
        out: list[int] = []
        node = self._head.forward[0]
        while node is not None and node.key is not None:
            out.append(node.key)
            node = node.forward[0]
        return out

    def last_visited(self) -> int:
        return self._visited

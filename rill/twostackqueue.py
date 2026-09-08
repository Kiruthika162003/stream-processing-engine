"""Two-stack queue: FIFO from two LIFO stacks, amortized constant despite the reversals.

Building a first-in-first-out queue from two last-in-first-out
stacks is a classic amortization result and a genuinely practical
one, because a queue backed by a naive array pays a linear cost
every time it dequeues from the front, shifting everything down.
Two stacks avoid that. New elements push onto an inbox stack, and
dequeues pop from an outbox stack; when the outbox is empty, the
entire inbox is poured into it, which reverses the order so the
oldest element, buried at the bottom of the inbox, ends up on top
of the outbox where a pop reaches it first. That pour is O(n) and
looks expensive, but it happens rarely and pays for itself:
between two pours every element is moved exactly once from inbox
to outbox, so across any sequence of operations each element is
pushed once, moved once, and popped once, three touches total,
which is amortized constant per operation even though individual
dequeues occasionally do the whole reversal. The trick is that the
costly reversal cannot happen again until the outbox drains and a
fresh batch has accumulated, so its cost is spread over the
dequeues that follow. This module runs the queue and counts the
element moves, so the amortized-constant claim is a measured total
against the operation count rather than an averaged hand-wave.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Missing


@dataclass
class TwoStackQueue:
    _inbox: list[str] = field(default_factory=list)
    _outbox: list[str] = field(default_factory=list)
    _moves: int = 0

    def enqueue(self, item: str) -> None:
        self._inbox.append(item)

    def dequeue(self) -> str:
        if not self._outbox:
            while self._inbox:
                self._outbox.append(self._inbox.pop())
                self._moves += 1
        if not self._outbox:
            raise Missing("queue is empty")
        return self._outbox.pop()

    def __len__(self) -> int:
        return len(self._inbox) + len(self._outbox)

    def moves(self) -> int:
        return self._moves

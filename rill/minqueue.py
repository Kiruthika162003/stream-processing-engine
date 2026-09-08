"""Min queue: the minimum of a FIFO in amortized constant time, from two min-stacks.

A queue that reports its current minimum is what a sliding-window
minimum needs, and neither a plain queue nor a single min-stack
gives it: a queue has no cheap minimum, and a min-stack tracks the
minimum of a LIFO, not a FIFO. The construction that works composes
the two ideas already built here, the two-stack queue and the min
stack. Keep two stacks, an inbox and an outbox, and make each a
min-stack that records the running minimum at every level. Enqueue
pushes onto the inbox min-stack; dequeue pops from the outbox, and
when the outbox is empty it pours the inbox over, which reverses
the order into FIFO and rebuilds the outbox's running minimums as
it goes. The current minimum of the whole queue is then the smaller
of the two stacks' top minimums, a constant-time read. The
amortized cost is constant because every element is pushed onto the
inbox once, moved to the outbox once, and popped once, the same
once-each accounting the two-stack queue already pays, now carrying
a running minimum along each stack. So enqueue, dequeue, and
minimum are all amortized constant, which turns a sliding-window
minimum into a sequence of enqueues and dequeues rather than a
rescan of the window. This module keeps the two min-stacks in
lockstep and answers the minimum from their tops, checked against a
naive model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Missing


@dataclass
class MinQueue:
    _inbox: list[tuple[int, int]] = field(default_factory=list)
    _outbox: list[tuple[int, int]] = field(default_factory=list)

    def enqueue(self, value: int) -> None:
        running = value if not self._inbox else min(value, self._inbox[-1][1])
        self._inbox.append((value, running))

    def dequeue(self) -> int:
        if not self._outbox:
            while self._inbox:
                value, _ = self._inbox.pop()
                running = value if not self._outbox else min(value, self._outbox[-1][1])
                self._outbox.append((value, running))
        if not self._outbox:
            raise Missing("dequeue from an empty queue")
        return self._outbox.pop()[0]

    def minimum(self) -> int:
        if not self._inbox and not self._outbox:
            raise Missing("no minimum of an empty queue")
        candidates = []
        if self._inbox:
            candidates.append(self._inbox[-1][1])
        if self._outbox:
            candidates.append(self._outbox[-1][1])
        return min(candidates)

    def __len__(self) -> int:
        return len(self._inbox) + len(self._outbox)

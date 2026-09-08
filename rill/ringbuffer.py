"""Ring buffer: a fixed window that either overwrites the oldest or refuses the newest.

A bounded circular buffer holds the last so-many items in fixed
memory, and what it does when full is the whole design decision.
In overwrite mode a push past capacity drops the oldest item to
make room, so the buffer never blocks and never grows and always
holds the most recent window, which is exactly right for
telemetry where an old sample is worthless and wrong for a work
queue where the dropped item was a job someone needed done. In
reject mode a push past capacity refuses the newest item instead,
which is right for the queue and wrong for telemetry, since it
freezes the buffer on stale data and turns away the fresh. There
is no full-buffer behavior that serves both, so the buffer makes
the choice explicit and, in overwrite mode, hands back the item
it dropped rather than losing it silently, so the caller that
cannot afford the loss finds out at the push and not in a
postmortem. This module implements the circular indexing, both
full-buffer policies, and an ordered snapshot from oldest to
newest, so the drop or the refusal is a return value a test can
hold.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid, Missing


@dataclass
class RingBuffer:
    capacity: int
    overwrite: bool = True
    _buf: list[str] = field(default_factory=list)
    _head: int = 0
    _count: int = 0

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise Invalid("capacity must be positive")
        self._buf = [""] * self.capacity

    def push(self, item: str) -> str | None:
        if self._count == self.capacity:
            if not self.overwrite:
                raise Halted("ring buffer is full and set to reject")
            dropped = self._buf[self._head]
            self._buf[self._head] = item
            self._head = (self._head + 1) % self.capacity
            return dropped
        tail = (self._head + self._count) % self.capacity
        self._buf[tail] = item
        self._count += 1
        return None

    def pop(self) -> str:
        if self._count == 0:
            raise Missing("ring buffer is empty")
        item = self._buf[self._head]
        self._head = (self._head + 1) % self.capacity
        self._count -= 1
        return item

    def snapshot(self) -> list[str]:
        return [
            self._buf[(self._head + offset) % self.capacity]
            for offset in range(self._count)
        ]

    def full(self) -> bool:
        return self._count == self.capacity

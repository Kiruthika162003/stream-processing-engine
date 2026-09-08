"""Priority inheritance: a low task holding a lock borrows the priority of who waits on it.

Priority inversion is the bug where a high-priority task is
blocked, in effect, by a lower-priority one. A low task takes a
lock, a high task needs the same lock and waits, and then a
medium task, needing no lock, preempts the low task because it
outranks it, so the low task cannot run to release the lock, so
the high task waits behind the medium one it outranks. The high
task's priority has been inverted by a task it should dominate,
and while the low holder is starved the wait is unbounded. The
fix is priority inheritance: while a low task holds a lock that a
higher task is waiting on, it temporarily inherits that higher
priority, so the medium task can no longer preempt it, the lock
is released promptly, and the high task waits only for the
critical section rather than for the whole medium workload. This
module models a lock that tracks its holder and waiters and
computes the holder's effective priority, raised to the highest
waiter when inheritance is on, so the difference between a holder
that a medium task can preempt and one it cannot is a comparison
a test can make rather than a race that shows up once in
production.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class PriorityLock:
    inherit: bool = True
    _holder: tuple[str, int] | None = None
    _waiters: list[tuple[str, int]] = field(default_factory=list)

    def acquire(self, task: str, priority: int) -> str:
        if self._holder is None:
            self._holder = (task, priority)
            return "held"
        self._waiters.append((task, priority))
        return "waiting"

    def release(self) -> None:
        if self._holder is None:
            raise Invalid("no holder to release the lock")
        if self._waiters:
            self._waiters.sort(key=lambda waiter: waiter[1], reverse=True)
            self._holder = self._waiters.pop(0)
        else:
            self._holder = None

    def holder_effective_priority(self) -> int:
        if self._holder is None:
            raise Invalid("the lock is free")
        base = self._holder[1]
        if self.inherit and self._waiters:
            return max(base, *(priority for _, priority in self._waiters))
        return base

    def can_preempt(self, priority: int) -> bool:
        return priority > self.holder_effective_priority()

"""Readers-writer lock: whichever side you give priority, the other side can starve.

A readers-writer lock lets any number of readers share the lock
while a writer holds it alone, which is the right model for state
read far more often than written. The hard part is not the mutual
exclusion, it is what happens when both keep arriving, and there
is no policy that is fair to everyone. Give writers priority, so a
reader must yield whenever a writer is waiting, and a steady
stream of writers starves the readers, which never find a moment
with no writer queued. Give readers priority, letting a new reader
in as long as any reader holds the lock, and a steady stream of
readers starves the writer, which never finds the reader count at
zero. The choice is a tradeoff between the two starvations, not a
way to avoid them, and picking it means knowing which side can
tolerate waiting: a writer that must land promptly wants writer
priority, a read path that must never block wants reader priority.
This module runs the lock under either policy and exposes whether
an acquire succeeds, so the starvation each policy imposes on the
other side is a state a test can demonstrate rather than a
deadlock discovered in production.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class RwLock:
    writer_priority: bool = True
    _readers: int = 0
    _writer: bool = False
    _waiting_writers: int = 0

    def acquire_read(self) -> bool:
        if self._writer:
            return False
        if self.writer_priority and self._waiting_writers > 0:
            return False
        self._readers += 1
        return True

    def release_read(self) -> None:
        if self._readers == 0:
            raise Invalid("no reader to release")
        self._readers -= 1

    def request_write(self) -> None:
        self._waiting_writers += 1

    def acquire_write(self) -> bool:
        if self._waiting_writers == 0:
            raise Invalid("a write must be requested before it is acquired")
        if self._writer or self._readers > 0:
            return False
        self._writer = True
        self._waiting_writers -= 1
        return True

    def release_write(self) -> None:
        if not self._writer:
            raise Invalid("no writer to release")
        self._writer = False

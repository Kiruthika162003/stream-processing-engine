"""Group commit: one fsync for a batch of writes, trading a little latency for throughput.

Durability means the write is on disk before the ack, which
means an fsync, and an fsync is expensive out of all proportion
to the bytes it flushes because it waits on the physical device.
One fsync per write caps a durable log's throughput at the disk's
fsync rate no matter how small the writes are, which for a stream
of tiny records is a catastrophe of syncing. Group commit breaks
the cap by noticing that a single fsync makes everything written
before it durable at once: pending writes accumulate, and when
the batch fills or a short timer fires the log issues one fsync
that commits the whole group, so the fsync cost is amortized
across the batch and the throughput rises by roughly the batch
size. The price is latency, since a write now waits for its
batch to fill or the timer to elapse before its ack, which is
why the batch size and the timer are a throughput-for-latency
dial and not a free win. This module accumulates writes, commits
on a full batch or a timed flush, and counts the fsyncs, so the
amortization is a measured ratio against the one-per-write floor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class GroupCommitLog:
    max_batch: int
    max_wait: int
    _pending: list[str] = field(default_factory=list)
    _oldest_at: int | None = None
    _fsyncs: int = 0
    _durable: int = 0

    def __post_init__(self) -> None:
        if self.max_batch < 1 or self.max_wait < 1:
            raise Invalid("batch and wait must be positive")

    def append(self, record: str, now: int) -> bool:
        self._pending.append(record)
        if self._oldest_at is None:
            self._oldest_at = now
        if len(self._pending) >= self.max_batch:
            self._commit()
            return True
        return False

    def tick(self, now: int) -> bool:
        if self._oldest_at is None:
            return False
        if now - self._oldest_at >= self.max_wait:
            self._commit()
            return True
        return False

    def _commit(self) -> None:
        if not self._pending:
            return
        self._durable += len(self._pending)
        self._pending.clear()
        self._oldest_at = None
        self._fsyncs += 1

    def fsyncs(self) -> int:
        return self._fsyncs

    def durable(self) -> int:
        return self._durable

    def pending(self) -> int:
        return len(self._pending)

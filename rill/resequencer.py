"""Resequencer: putting the stream back in order, and the gap that waits forever.

Messages that were sent in order arrive out of order once a
network or a partitioned queue has had its way with them, and a
resequencer restores the order by buffering what arrives early
and releasing only the contiguous run that starts at the next
expected sequence. The design works until a message is not late
but lost, and then the resequencer waits for a sequence that is
never coming while every message behind it piles up in the
buffer, the head-of-line stall that turns one dropped packet into
a frozen stream. The gap timeout is the escape: a missing
sequence that has not arrived within the timeout is declared lost,
the resequencer skips it, and the buffered run behind it is
released, trading a permanent hole in the order for a stream that
moves again. This module tracks the next expected sequence,
buffers the out-of-order arrivals, releases the contiguous runs,
and on a timed-out gap steps over the missing sequence rather
than holding the whole stream hostage to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Resequencer:
    gap_timeout: int
    _next: int = 0
    _buffer: dict[int, str] = field(default_factory=dict)
    _first_gap_seen: int | None = None
    _skipped: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.gap_timeout <= 0:
            raise Invalid("gap timeout must be positive")

    def offer(self, sequence: int, payload: str, now: int) -> list[str]:
        if sequence < self._next:
            raise Invalid(f"sequence {sequence} already released")
        self._buffer[sequence] = payload
        if self._next not in self._buffer and self._first_gap_seen is None:
            self._first_gap_seen = now
        return self._release()

    def _release(self) -> list[str]:
        out: list[str] = []
        while self._next in self._buffer:
            out.append(self._buffer.pop(self._next))
            self._next += 1
            self._first_gap_seen = None
        return out

    def tick(self, now: int) -> list[str]:
        if self._next in self._buffer or not self._buffer:
            return []
        if self._first_gap_seen is None:
            self._first_gap_seen = now
            return []
        if now - self._first_gap_seen < self.gap_timeout:
            return []
        self._skipped.append(self._next)
        self._next += 1
        return self._release()

    def pending(self) -> int:
        return len(self._buffer)

    def skipped(self) -> list[int]:
        return list(self._skipped)

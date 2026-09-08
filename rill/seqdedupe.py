"""Idempotent producer sequences: the retry after a lost ack must not write twice.

An idempotent producer stamps each record with a sequence number
and the broker remembers the last sequence it accepted per
producer, which turns the ordinary retry into a safe one. When a
record is written but its ack is lost, the producer retries the
same sequence, and the broker, seeing a sequence it has already
accepted, acknowledges it again without writing it a second time,
so the duplicate the lost ack would have caused never lands. The
sequence has to be checked three ways, not one. A sequence one
past the last is the next record and is accepted. A sequence at
or below the last is a retry and is acked idempotently, no second
write. A sequence more than one past the last is a gap, a record
that went missing between this one and the last accepted, and it
must be rejected loudly rather than accepted, because accepting it
silently masks the lost record and breaks the exactly-once chain
the sequences exist to hold. This module tracks the last accepted
sequence per producer and classifies every write against it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

ACCEPTED = "accepted"
DUPLICATE = "duplicate"


@dataclass
class SequenceBroker:
    _last: dict[str, int] = field(default_factory=dict)

    def write(self, producer: str, sequence: int, _payload: str) -> str:
        if sequence < 0:
            raise Invalid("sequence cannot be negative")
        last = self._last.get(producer, -1)
        if sequence <= last:
            return DUPLICATE
        if sequence > last + 1:
            raise Invalid(
                f"{producer} sequence {sequence} skips past {last + 1}; "
                "a record went missing and accepting this masks it"
            )
        self._last[producer] = sequence
        return ACCEPTED

    def last_accepted(self, producer: str) -> int:
        return self._last.get(producer, -1)

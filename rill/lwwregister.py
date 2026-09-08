"""LWW-Register: the simplest mergeable value, and the write it quietly discards.

A last-writer-wins register is the cheapest conflict-free value:
it holds one entry stamped with a timestamp, a write with a newer
timestamp replaces it, and the merge of two replicas keeps the
one with the higher stamp. Simplicity has a price the counter and
the set do not pay. When two replicas write concurrently the
register keeps exactly one and throws the other away, so a value
someone wrote is silently lost, which is fine for a field like a
display name where the latest intent is all that matters and
wrong for anything where both writes carry information. The one
subtlety that keeps LWW correct rather than merely simple is the
tie: two writes can carry the same timestamp, and if the replicas
break that tie differently they diverge forever, so the tiebreak
must be deterministic, here the writer's node id, so every
replica resolves an identical clash to the identical winner. This
module holds the stamped value, applies the newer write, merges
by the higher stamp with the id as tiebreak, and names the
discarded write, so the data loss LWW trades for its simplicity
is visible rather than assumed away.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class LWWRegister:
    node: str
    _value: str | None = None
    _stamp: int = -1
    _writer: str = ""

    def _beats(self, stamp: int, writer: str) -> bool:
        return (stamp, writer) > (self._stamp, self._writer)

    def write(self, value: str, stamp: int) -> None:
        if stamp < 0:
            raise Invalid("stamp cannot be negative")
        if self._beats(stamp, self.node):
            self._value = value
            self._stamp = stamp
            self._writer = self.node

    def merge(self, other: LWWRegister) -> str | None:
        discarded = None
        if other._value is not None and self._beats(other._stamp, other._writer):
            discarded = self._value
            self._value = other._value
            self._stamp = other._stamp
            self._writer = other._writer
        elif self._value is not None and other._value is not None:
            discarded = other._value
        return discarded

    def value(self) -> str | None:
        return self._value

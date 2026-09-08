"""Epoch fencing: the presumed-dead producer that wakes up and is told it is stale.

A transactional producer registers under a transactional id and
is handed an epoch. When it is presumed dead and a replacement
registers under the same id, the coordinator bumps the epoch and
the replacement carries the higher number. Fencing is the rule
that any write tagged with an epoch below the current one is
rejected, and it exists for the case that looks impossible until
it happens: the old producer was not dead, only slow or
partitioned, and it wakes up mid-write believing it still owns
the id. Without fencing that zombie and its replacement both
write, and the same logical output lands twice from two
producers that each think they are alone, the split brain that
duplicates transactions no downstream dedupe was told to expect.
With fencing the zombie's first write after the takeover is
refused because its epoch is stale, so exactly one producer is
live per id at any instant. This module tracks the current epoch
per id, bumps it on takeover, and fences every write that
carries a stale epoch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid


@dataclass
class FencingCoordinator:
    _epoch: dict[str, int] = field(default_factory=dict)

    def register(self, txn_id: str) -> int:
        current = self._epoch.get(txn_id)
        self._epoch[txn_id] = 0 if current is None else current + 1
        return self._epoch[txn_id]

    def current_epoch(self, txn_id: str) -> int:
        if txn_id not in self._epoch:
            raise Invalid(f"no producer registered for {txn_id}")
        return self._epoch[txn_id]

    def write(self, txn_id: str, epoch: int, payload: str) -> str:
        current = self.current_epoch(txn_id)
        if epoch < current:
            raise Halted(
                f"{txn_id} epoch {epoch} is fenced; a producer at "
                f"epoch {current} has taken over"
            )
        if epoch > current:
            raise Invalid(f"{txn_id} epoch {epoch} is ahead of the coordinator")
        return f"{txn_id}@{epoch}: {payload}"

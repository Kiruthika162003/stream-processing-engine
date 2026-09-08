"""The transactional sink: results land in epochs, or not at all.

At-least-once delivery plus an external sink equals duplicate
rows in someone's database, unless the sink writes in epochs:
results accumulate in a pending epoch, the checkpoint that
covers them completes, and only then does the epoch commit,
atomically, tagged with its number so the sink can refuse an
epoch it has already seen. The two-step is the whole
guarantee: a crash after processing but before commit leaves
a pending epoch that recovery discards and replays, and a
crash after commit leaves a committed epoch the replay
recognizes and skips, so every result reaches the sink
exactly once not because the network improved but because
the sink learned to count. The drill crashes at both points
and reads the sink after each recovery, which is the only
audit that means anything: the rows themselves, counted once.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid


@dataclass
class EpochSink:
    committed_rows: list[str] = field(default_factory=list)
    committed_epochs: set[int] = field(default_factory=set)
    pending: dict[int, list[str]] = field(default_factory=dict)
    refused_replays: int = 0

    def stage(self, epoch: int, row: str) -> None:
        if epoch in self.committed_epochs:
            raise Halted(
                f"epoch {epoch} is committed; staging into it "
                "would edit history"
            )
        self.pending.setdefault(epoch, []).append(row)

    def commit(self, epoch: int) -> str:
        if epoch in self.committed_epochs:
            self.refused_replays += 1
            return (
                f"epoch {epoch} already committed; the replay "
                "is recognized and skipped, because the sink "
                "learned to count"
            )
        rows = self.pending.pop(epoch, [])
        if not rows:
            raise Invalid(
                f"epoch {epoch} has nothing staged; an empty "
                "commit is a checkpoint misfire"
            )
        self.committed_rows.extend(rows)
        self.committed_epochs.add(epoch)
        return (
            f"epoch {epoch} committed atomically: "
            f"{len(rows)} row(s) land together"
        )

    def crash_recovery(self) -> str:
        discarded = sum(
            len(rows) for rows in self.pending.values()
        )
        epochs = sorted(self.pending)
        self.pending.clear()
        if discarded == 0:
            return "nothing pending; the crash cost nothing"
        return (
            f"recovery discards {discarded} pending row(s) "
            f"from epoch(s) {epochs}; they will be replayed "
            "and land exactly once"
        )

    def audit(self) -> str:
        distinct = len(set(self.committed_rows))
        total = len(self.committed_rows)
        if distinct != total:
            return (
                f"DUPLICATES: {total - distinct} row(s) landed "
                "twice; the machinery failed its one job"
            )
        return (
            f"{total} row(s), each exactly once, "
            f"{self.refused_replays} replay(s) refused; the "
            "rows themselves are the only audit that means "
            "anything"
        )

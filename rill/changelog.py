"""The state changelog: every mutation shipped, so recovery is a read.

Checkpoint snapshots capture state at intervals; the
changelog captures it continuously, every put and delete
appended to a log as it happens, so a failed worker's
replacement restores by replaying the changelog instead of
waiting for the last snapshot plus a reprocessing gap. The
restore cost is the changelog's length, which grows forever
unless truncated, and the truncation rule is the safe one:
everything before the latest snapshot is redundant, because
the snapshot already contains its effects, so the changelog
keeps only the suffix and the restore is snapshot plus
suffix, bounded by the checkpoint interval. The drill
measures the restore both ways, full replay against snapshot
plus suffix, and the ratio is the argument for paying the
snapshot's cost, stated in records replayed rather than
faith.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

TOMBSTONE = None


@dataclass
class Changelog:
    entries: list[tuple[int, str, int | None]] = field(
        default_factory=list
    )
    snapshots: dict[int, dict[str, int]] = field(
        default_factory=dict
    )
    truncated_before: int = 0

    def record_put(
        self, sequence: int, key: str, value: int
    ) -> None:
        self._append(sequence, key, value)

    def record_delete(self, sequence: int, key: str) -> None:
        self._append(sequence, key, TOMBSTONE)

    def _append(
        self, sequence: int, key: str, value: int | None
    ) -> None:
        if self.entries and sequence <= self.entries[-1][0]:
            raise Invalid("sequences only grow")
        if not key:
            raise Invalid("state has keys")
        self.entries.append((sequence, key, value))

    def snapshot(self, sequence: int) -> str:
        state = self._replay(self.entries)
        self.snapshots[sequence] = state
        before = len(self.entries)
        self.entries = [
            entry
            for entry in self.entries
            if entry[0] > sequence
        ]
        self.truncated_before = sequence
        return (
            f"snapshot at {sequence}: {len(state)} key(s) "
            f"captured, {before - len(self.entries)} "
            "changelog record(s) now redundant and truncated"
        )

    @staticmethod
    def _replay(
        entries: list[tuple[int, str, int | None]],
        base: dict[str, int] | None = None,
    ) -> dict[str, int]:
        state = dict(base or {})
        for _, key, value in entries:
            if value is TOMBSTONE:
                state.pop(key, None)
            else:
                state[key] = value
        return state

    def restore(self) -> tuple[dict[str, int], str]:
        if not self.snapshots:
            state = self._replay(self.entries)
            return state, (
                f"no snapshot: full replay of "
                f"{len(self.entries)} record(s)"
            )
        latest = max(self.snapshots)
        state = self._replay(
            self.entries, base=self.snapshots[latest]
        )
        return state, (
            f"snapshot at {latest} plus "
            f"{len(self.entries)} suffix record(s); bounded "
            "by the checkpoint interval, not the job's age"
        )

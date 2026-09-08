"""Log compaction: keep the latest truth per key, and bury with a marker.

Some logs are histories and some are ledgers of current
state, and compaction converts the first into the second:
for every key, only the newest record survives, because a
consumer restoring state needs where things stand, not the
full biography of how they got there. Deletion inside a
compacted log is its own discipline: removing a key's records
would leave restorers believing the key never existed, so
deletion writes a tombstone, a marker that says this key is
gone on purpose, and the tombstone itself must survive long
enough for every restorer to have seen it before it too is
swept, since a tombstone swept early resurrects the deleted
key on the next restore from an older reader. The compaction
report prices the squeeze, records before and after, and
counts the tombstones still standing guard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

TOMBSTONE = "__tombstone__"


@dataclass
class CompactedLog:
    records: list[tuple[str, str, int]] = field(
        default_factory=list
    )
    tombstone_grace: int = 50

    def append(self, key: str, value: str, offset: int) -> None:
        if not key:
            raise Invalid("a compacted log routes by key")
        if self.records and offset <= self.records[-1][2]:
            raise Invalid("offsets only grow")
        self.records.append((key, value, offset))

    def delete(self, key: str, offset: int) -> str:
        self.append(key, TOMBSTONE, offset)
        return (
            f"{key} buried with a marker at {offset}; gone on "
            "purpose is different from never existed"
        )

    def compact(self, now_offset: int) -> str:
        before = len(self.records)
        latest: dict[str, tuple[str, int]] = {}
        for key, value, offset in self.records:
            latest[key] = (value, offset)
        survivors = []
        swept_tombstones = 0
        for key, (value, offset) in latest.items():
            if value == TOMBSTONE and (
                now_offset - offset > self.tombstone_grace
            ):
                swept_tombstones += 1
                continue
            survivors.append((key, value, offset))
        survivors.sort(key=lambda record: record[2])
        self.records = survivors
        standing = sum(
            1 for _, value, _ in survivors if value == TOMBSTONE
        )
        return (
            f"{before} record(s) squeezed to "
            f"{len(survivors)}, {standing} tombstone(s) still "
            f"standing guard, {swept_tombstones} swept past "
            "their grace"
        )

    def restore(self) -> dict[str, str]:
        state: dict[str, str] = {}
        for key, value, _ in self.records:
            if value == TOMBSTONE:
                state.pop(key, None)
            else:
                state[key] = value
        return state

    def resurrection_check(
        self, restored: dict[str, str], deleted_keys: set[str]
    ) -> str:
        ghosts = sorted(
            key for key in deleted_keys if key in restored
        )
        if ghosts:
            return (
                f"RESURRECTION: {', '.join(ghosts)} came back; "
                "a tombstone was swept before every restorer "
                "had seen it"
            )
        return "the deleted stay deleted; the grace period held"

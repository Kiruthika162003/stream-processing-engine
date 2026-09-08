"""MVCC: a reader pinned to a snapshot sees one consistent world, not a moving one.

A read that spans time in a mutating store sees a moving target:
a value read early and re-read late can have changed underneath,
and a scan across many keys can catch some before a write and
others after, returning a mix that was never a real state of the
store. Multiversion concurrency control fixes this by never
overwriting. Each write appends a new version stamped with its
commit time, and a reader takes a snapshot timestamp and sees,
for every key, the latest version committed at or before that
timestamp and nothing newer, so its whole read reflects one
instant no matter how long it takes or how much is written while
it runs. Two readers at different snapshots see different but each
internally consistent worlds, which is exactly the repeatable
read a single mutable cell cannot offer. The cost is that old
versions accumulate until they can be reclaimed, and a version is
safe to drop only once no live snapshot could still need it, so
the oldest active snapshot sets the garbage-collection horizon.
This module keeps the versions, answers a read as of a snapshot,
and computes which versions a horizon makes collectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid, Missing


@dataclass
class MvccStore:
    _versions: dict[str, list[tuple[int, str]]] = field(default_factory=dict)

    def write(self, key: str, value: str, commit_ts: int) -> None:
        chain = self._versions.setdefault(key, [])
        if chain and commit_ts <= chain[-1][0]:
            raise Invalid(
                f"commit_ts {commit_ts} not after the last version at {chain[-1][0]}"
            )
        chain.append((commit_ts, value))

    def read(self, key: str, snapshot_ts: int) -> str:
        chain = self._versions.get(key, [])
        visible = [value for ts, value in chain if ts <= snapshot_ts]
        if not visible:
            raise Missing(f"{key} has no version visible at {snapshot_ts}")
        return visible[-1]

    def collectable(self, horizon_ts: int) -> int:
        total = 0
        for chain in self._versions.values():
            covered = [ts for ts, _ in chain if ts <= horizon_ts]
            if len(covered) > 1:
                total += len(covered) - 1
        return total

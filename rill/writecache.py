"""Write-back versus write-through: coalescing writes against losing the ones not yet flushed.

A cache in front of a slow backing store has to decide what a
write does. Write-through sends every write to the store as it
happens, so the store is always current and a crash loses
nothing, but the store takes the full write traffic and the write
is only as fast as the store. Write-back writes to the cache
alone, marks the entry dirty, and pushes dirty entries to the
store later in a batch, which makes writes fast and, crucially,
coalesces repeated writes to the same key into a single store
write, since only the latest value of a dirty key is ever
flushed. The saving is real, and so is the exposure: a crash
between a write and the next flush loses every dirty entry that
had not reached the store, because those values lived only in the
cache. So the choice is coalesced, fast writes with a window of
loss, against durable, slower writes with none, and it turns on
whether the data can tolerate losing the last unflushed batch. A
write-heavy workload hammering a few hot keys wants write-back for
the coalescing; a workload that must not lose an
acknowledged write wants write-through. This module runs both,
counting store writes and, for write-back, the dirty entries a
crash would lose, so the trade is a measured pair.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class WriteThroughCache:
    _cache: dict[str, str] = field(default_factory=dict)
    _store_writes: int = 0

    def write(self, key: str, value: str) -> None:
        self._cache[key] = value
        self._store_writes += 1

    def store_writes(self) -> int:
        return self._store_writes


@dataclass
class WriteBackCache:
    _cache: dict[str, str] = field(default_factory=dict)
    _dirty: set[str] = field(default_factory=set)
    _store_writes: int = 0

    def write(self, key: str, value: str) -> None:
        self._cache[key] = value
        self._dirty.add(key)

    def flush(self) -> int:
        flushed = len(self._dirty)
        self._store_writes += flushed
        self._dirty.clear()
        return flushed

    def crash(self) -> int:
        lost = len(self._dirty)
        self._dirty.clear()
        return lost

    def store_writes(self) -> int:
        return self._store_writes

    def read(self, key: str) -> str:
        if key not in self._cache:
            raise Invalid(f"no key {key}")
        return self._cache[key]

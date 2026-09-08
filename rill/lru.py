"""LRU cache: recency is a good guess until a scan larger than the cache poisons it.

Least-recently-used eviction bets that the key touched longest
ago is the one least likely to be touched next, which holds
beautifully for skewed access where a small working set is hit
over and over, and fails exactly on a scan. A single pass over
more distinct keys than the cache holds touches each once, marks
each most-recently-used in turn, and so evicts the entire prior
working set to make room for keys that will never be seen again,
leaving the cache full of the scan's leavings and cold for the
real workload that resumes after it. The scan poisons the cache,
and the poisoning is not a bug in the LRU, it is LRU doing
precisely what it was told: treat the most recent touch as the
most valuable. Scan-resistant policies exist because of this,
holding a key back until it has been seen more than once so a
one-time scan cannot promote its keys over a proven working set.
This module implements the LRU with its recency ordering and
eviction, and counts hits and misses, so the thrash a scan
inflicts is a measured collapse in hit rate rather than a warning
in the documentation.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field

from rill.errors import Invalid

MISS = object()


@dataclass
class LruCache:
    capacity: int
    _data: OrderedDict[str, str] = field(default_factory=OrderedDict)
    _hits: int = 0
    _misses: int = 0

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise Invalid("capacity must be positive")

    def get(self, key: str) -> str | None:
        if key not in self._data:
            self._misses += 1
            return None
        self._hits += 1
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: str, value: str) -> str | None:
        evicted = None
        if key in self._data:
            self._data.move_to_end(key)
        elif len(self._data) >= self.capacity:
            evicted, _ = self._data.popitem(last=False)
        self._data[key] = value
        return evicted

    def keys(self) -> list[str]:
        return list(self._data)

    def hit_rate(self) -> float:
        total = self._hits + self._misses
        if total == 0:
            raise Invalid("no accesses yet")
        return self._hits / total

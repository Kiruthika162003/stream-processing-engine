"""TinyLFU admission: a newcomer gets in only if it is hotter than who it would evict.

An LRU cache is poisoned by a scan because it admits every key
unconditionally and lets recency alone decide the victim, so a
one-time scan evicts a proven working set to cache keys that will
never be seen again. TinyLFU adds an admission filter in front of
the eviction. It keeps a frequency estimate of what the cache has
seen, and when the cache is full and a new key wants in, it does
not simply evict the least-recently-used victim; it compares the
newcomer's frequency to the victim's and admits the newcomer only
if it is the more frequent of the two. A scan key seen once has a
frequency of one and cannot displace a working-set key that has
been hit many times, so the scan washes over the cache without
disturbing the hot set, exactly the failure the plain LRU could
not resist. The frequency estimate is the whole mechanism, and
the trade is that a genuinely new but soon-to-be-hot key can be
turned away on its first appearance before it has built up any
frequency. This module keeps the frequencies and the recency
order and admits on the comparison, so the scan resistance the
LRU lacked is a measured survival count.
"""

from __future__ import annotations

from collections import Counter, OrderedDict
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class TinyLfuCache:
    capacity: int
    _freq: Counter = field(default_factory=Counter)
    _data: OrderedDict[str, str] = field(default_factory=OrderedDict)

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise Invalid("capacity must be positive")

    def _touch(self, key: str) -> None:
        self._freq[key] += 1

    def get(self, key: str) -> str | None:
        self._touch(key)
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: str, value: str) -> str | None:
        self._touch(key)
        if key in self._data:
            self._data.move_to_end(key)
            self._data[key] = value
            return None
        if len(self._data) < self.capacity:
            self._data[key] = value
            return None
        victim = next(iter(self._data))
        if self._freq[key] > self._freq[victim]:
            self._data.popitem(last=False)
            self._data[key] = value
            return victim
        return key

    def keys(self) -> list[str]:
        return list(self._data)

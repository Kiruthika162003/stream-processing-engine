"""Cuckoo filter: an approximate set that a Bloom filter's one weakness cannot match, deletion.

A Bloom filter answers membership in tiny space and can never
delete, because its bits are shared across items and clearing one
item's bits would clear others' too, so a Bloom filter that has
to forget entries is the wrong structure. A cuckoo filter keeps
the small footprint and adds deletion by storing a short
fingerprint of each item in one of two candidate buckets. The
second bucket is the first exclusive-or a hash of the fingerprint,
an involution, so from either bucket the other is one cheap
computation away, which is what lets an insert into two full
buckets kick an existing fingerprint to its alternate and make
room, cuckoo-style, and what lets a delete find and remove a
fingerprint from whichever of its two buckets holds it. The
trade against Bloom is that inserts can fail: when the kick chain
runs its whole budget without finding a free slot the filter is
too full to accept more, a loud failure at a load factor rather
than a silent degradation. This module fingerprints, places and
kicks, tests, and deletes, so the property Bloom cannot offer is
a passing test and its price is a measured insertion limit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_digest
from rill.errors import Halted, Invalid


def _hash(text: str) -> int:
    return int(stable_digest(text)[:8], 16)


@dataclass
class CuckooFilter:
    buckets: int
    slots: int = 4
    max_kicks: int = 20
    _table: list[list[int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.buckets < 1 or self.buckets & (self.buckets - 1):
            raise Invalid("buckets must be a power of two")
        if self.slots < 1:
            raise Invalid("slots must be positive")
        self._table = [[] for _ in range(self.buckets)]

    def _fingerprint(self, item: str) -> int:
        return _hash("fp:" + item) % 255 + 1

    def _index1(self, item: str) -> int:
        return _hash("ix:" + item) % self.buckets

    def _alternate(self, index: int, fingerprint: int) -> int:
        return index ^ (_hash("alt:" + str(fingerprint)) % self.buckets)

    def add(self, item: str) -> None:
        fingerprint = self._fingerprint(item)
        i1 = self._index1(item)
        i2 = self._alternate(i1, fingerprint)
        for index in (i1, i2):
            if len(self._table[index]) < self.slots:
                self._table[index].append(fingerprint)
                return
        index = i1
        for _ in range(self.max_kicks):
            victim = self._table[index].pop(0)
            self._table[index].append(fingerprint)
            fingerprint = victim
            index = self._alternate(index, fingerprint)
            if len(self._table[index]) < self.slots:
                self._table[index].append(fingerprint)
                return
        raise Halted("cuckoo filter is too full; the kick chain gave up")

    def contains(self, item: str) -> bool:
        fingerprint = self._fingerprint(item)
        i1 = self._index1(item)
        i2 = self._alternate(i1, fingerprint)
        return fingerprint in self._table[i1] or fingerprint in self._table[i2]

    def delete(self, item: str) -> bool:
        fingerprint = self._fingerprint(item)
        i1 = self._index1(item)
        i2 = self._alternate(i1, fingerprint)
        for index in (i1, i2):
            if fingerprint in self._table[index]:
                self._table[index].remove(fingerprint)
                return True
        return False

    def load(self) -> int:
        return sum(len(bucket) for bucket in self._table)

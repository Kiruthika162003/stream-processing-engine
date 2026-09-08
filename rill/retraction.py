"""Retraction streams: a sum updates on a delete for free, a max has to look again.

A changelog stream carries not just inserts but retractions, a
row that was counted and is now withdrawn, and a materialized
aggregate over it must handle both. Whether a delete is cheap
depends entirely on whether the aggregate can be inverted. A sum
or a count is a group under addition: retracting a value is
subtracting it, an O(1) update that needs no memory of the other
values, so a sum over a retraction stream stays a single running
number. A maximum has no such inverse. Retracting the current
maximum tells you the largest value is gone but not what the new
largest is, because that fact lived in the values you did not
keep, so a max over a retraction stream cannot be a single number;
it must retain enough of the multiset to find the next maximum
when the current one is withdrawn, and retracting the max costs a
search of what remains rather than a subtraction. This module
holds a retractable sum that updates in constant time and a
retractable max that keeps a multiset and recomputes on the
retraction of its top, so the difference between an invertible
aggregate and a holistic one is the difference between an O(1)
delete and one that has to look again, made concrete.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class RetractableSum:
    _total: float = 0.0
    _count: int = 0

    def insert(self, value: float) -> None:
        self._total += value
        self._count += 1

    def retract(self, value: float) -> None:
        if self._count == 0:
            raise Invalid("nothing to retract")
        self._total -= value
        self._count -= 1

    def total(self) -> float:
        return self._total


@dataclass
class RetractableMax:
    _multiset: Counter = field(default_factory=Counter)
    _recomputes: int = 0

    def insert(self, value: int) -> None:
        self._multiset[value] += 1

    def retract(self, value: int) -> None:
        if self._multiset[value] == 0:
            raise Invalid(f"cannot retract {value}; it is not present")
        was_max = value == self.maximum()
        self._multiset[value] -= 1
        if self._multiset[value] == 0:
            del self._multiset[value]
        if was_max:
            self._recomputes += 1

    def maximum(self) -> int:
        if not self._multiset:
            raise Invalid("no values")
        return max(self._multiset)

    def recomputes(self) -> int:
        return self._recomputes

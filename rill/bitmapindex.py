"""Bitmap index: equality and range queries become set operations, not row scans.

A low-cardinality column, a status or a category, indexes well as
one bitmap per distinct value, where the bitmap's set bits are the
rows holding that value. The queries that would otherwise scan
every row become bit-parallel set operations over these bitmaps.
Matching a single value is just that value's bitmap. Matching any
of several values is the union of their bitmaps. Excluding a value
is its bitmap's complement against all rows. Combining a filter on
one column with a filter on another is the intersection of the two
columns' bitmaps, computed as a set operation rather than a nested
scan. Because the column has few distinct values, the total bitmap
storage is small, and because the operations are unions and
intersections, a query touches a number of bitmaps proportional to
the values it mentions rather than the rows it filters. The tradeoff
is that a high-cardinality column, a unique id, would have as many
bitmaps as rows and index badly, which is why bitmap indexes are a
tool for the categorical columns, not the keys. This module keeps
the per-value row sets and answers equality, union, complement, and
intersection, checking each against a brute-force scan so the set
algebra is shown to compute the same rows the scan would.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class BitmapIndex:
    _rows: int = 0
    _bitmaps: dict[str, set[int]] = field(default_factory=dict)

    def add(self, value: str) -> int:
        row = self._rows
        self._bitmaps.setdefault(value, set()).add(row)
        self._rows += 1
        return row

    def equals(self, value: str) -> set[int]:
        return set(self._bitmaps.get(value, set()))

    def any_of(self, values: list[str]) -> set[int]:
        result: set[int] = set()
        for value in values:
            result |= self._bitmaps.get(value, set())
        return result

    def complement(self, value: str) -> set[int]:
        return set(range(self._rows)) - self._bitmaps.get(value, set())

    def both(self, other: BitmapIndex, value: str, other_value: str) -> set[int]:
        if self._rows != other._rows:
            raise Invalid("indexes cover different row counts")
        return self.equals(value) & other.equals(other_value)

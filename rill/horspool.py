"""Boyer-Moore-Horspool: skipping ahead by whole patterns, examining fewer than n characters.

KMP and Rabin-Karp both examine every character of the text.
Horspool does better on average by examining fewer than all of
them, because it aligns the pattern and compares from the right
end, and on a mismatch it slides the pattern forward by a distance
read from a precomputed table keyed on the text character that sat
under the pattern's last position. If that character does not
occur in the pattern at all, the pattern jumps its whole length,
skipping a full window of the text unexamined, which is what makes
the average case sublinear: on a large alphabet most mismatches
land on a character absent from the pattern and the search leaps
by the pattern length each time. The skip table stores, for each
character, the distance from its last occurrence in the pattern to
the pattern's end, defaulting to the pattern length for characters
the pattern does not contain, and that distance is exactly how far
the pattern can slide without missing a possible match. The worst
case, a pattern and text over a tiny alphabet with heavy overlap,
degrades to the product of the lengths, but the everyday case of
searching natural text runs faster than the scan-everything
methods. This module builds the skip table, searches, and counts
the characters it actually compared, so the sublinear skipping is
a measured number against the text length.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class HorspoolSearch:
    pattern: str
    _comparisons: int = 0

    def __post_init__(self) -> None:
        if not self.pattern:
            raise Invalid("pattern cannot be empty")

    def _skip_table(self) -> dict[str, int]:
        m = len(self.pattern)
        table: dict[str, int] = {}
        for index in range(m - 1):
            table[self.pattern[index]] = m - 1 - index
        return table

    def find(self, text: str) -> list[int]:
        self._comparisons = 0
        m, n = len(self.pattern), len(text)
        if m > n:
            return []
        table = self._skip_table()
        hits: list[int] = []
        start = 0
        while start <= n - m:
            index = m - 1
            while index >= 0:
                self._comparisons += 1
                if text[start + index] != self.pattern[index]:
                    break
                index -= 1
            if index < 0:
                hits.append(start)
            start += table.get(text[start + m - 1], m)
        return hits

    def comparisons(self) -> int:
        return self._comparisons

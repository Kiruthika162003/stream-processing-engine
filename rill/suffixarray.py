"""Suffix array: all suffixes of a string in sorted order, built by doubling ranks.

The suffix array of a string is the list of its suffixes' starting
positions, ordered as the suffixes would sort lexicographically. It
is a compact index: with it, every occurrence of a pattern is a
contiguous block in the array, found by binary search, and it
underlies substring search, longest repeated substring, and more,
using far less memory than a suffix tree. Sorting the suffixes
directly is quadratic or worse, because each comparison can scan a
whole suffix. Prefix doubling avoids that. It sorts the suffixes by
their first character, then uses that ranking to sort by their first
two characters, then four, then eight, doubling the compared prefix
length each round. The trick that makes each round cheap is that a
suffix's rank by its first two-to-the-k characters is captured by a
pair: its own rank over the first half of that span and the rank of
the suffix two-to-the-k-minus-one positions later over the second
half, both already computed in the previous round. Sorting those
pairs re-ranks everyone, and after log n rounds the compared prefix
exceeds the string length so the ranking is total and final. Each
round sorts n pairs, so the cost is n log-squared n with an ordinary
sort, or n log n with a radix sort on the pairs. The finding worth
stating is that doubling turns the unbounded-length suffix
comparison into a fixed comparison of two small ranks, which is the
whole reason the construction is near-linear rather than quadratic.
This module builds the suffix array by doubling and searches it for a
pattern, and a test checks the array against the brute sorted
suffixes and the search against a scan, so the doubling is confirmed.
"""

from __future__ import annotations

from bisect import bisect_left
from itertools import pairwise

from rill.errors import Invalid


def suffix_array(text: str) -> list[int]:
    if text is None:
        raise Invalid("text must not be None")
    n = len(text)
    if n == 0:
        return []
    sa = list(range(n))
    rank = [ord(c) for c in text]
    tmp = [0] * n
    k = 1
    while True:
        def key(i: int, rank: list[int] = rank, k: int = k) -> tuple[int, int]:
            second = rank[i + k] if i + k < n else -1
            return (rank[i], second)

        sa.sort(key=key)
        tmp[sa[0]] = 0
        for a, b in pairwise(sa):
            tmp[b] = tmp[a] + (1 if key(a) < key(b) else 0)
        rank = tmp[:]
        if rank[sa[-1]] == n - 1:
            break
        k *= 2
    return sa


def search(text: str, pattern: str, sa: list[int]) -> list[int]:
    if pattern == "":
        raise Invalid("pattern must not be empty")
    suffixes_key = [text[i:] for i in sa]
    lo = bisect_left(suffixes_key, pattern)
    matches = []
    i = lo
    while i < len(suffixes_key) and suffixes_key[i].startswith(pattern):
        matches.append(sa[i])
        i += 1
    return sorted(matches)

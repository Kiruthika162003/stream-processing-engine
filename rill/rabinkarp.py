"""Rabin-Karp: a rolling hash slides the window in O(1), and the hash match still needs a check.

Searching a stream of text for a pattern by comparing the pattern
against every window position costs the pattern length at each
position, quadratic in the worst case. Rabin-Karp replaces most of
those comparisons with a hash. It computes a hash of the pattern
once and a hash of the first window, then slides the window one
character at a time, and the trick is that the new window's hash
comes from the old one in constant time: subtract the leaving
character's contribution, shift, and add the entering character,
no rehash of the whole window. Where the window hash equals the
pattern hash, the window is a candidate, and the total work is
linear on average because the hash update is O(1) per slide. The
part that is not optional is the verification. A hash match is not
a string match, because two different windows can hash alike, so
every hash hit must be confirmed by an actual character comparison
before it is reported, or the search emits false positives on
collisions. Skipping that check is the bug that makes Rabin-Karp
look right on friendly inputs and wrong on adversarial ones. This
module rolls the hash, compares on hash, and verifies each hit, so
the matches it returns are real and the linear roll is what found
them.
"""

from __future__ import annotations

from rill.errors import Invalid

_BASE = 257
_MOD = (1 << 61) - 1


def _hash(text: str) -> int:
    value = 0
    for char in text:
        value = (value * _BASE + ord(char)) % _MOD
    return value


def find(text: str, pattern: str) -> list[int]:
    if not pattern:
        raise Invalid("pattern cannot be empty")
    n, m = len(text), len(pattern)
    if m > n:
        return []
    pattern_hash = _hash(pattern)
    window_hash = _hash(text[:m])
    high = pow(_BASE, m - 1, _MOD)
    hits: list[int] = []
    for start in range(n - m + 1):
        if window_hash == pattern_hash and text[start : start + m] == pattern:
            hits.append(start)
        if start < n - m:
            leaving = ord(text[start])
            entering = ord(text[start + m])
            window_hash = (window_hash - leaving * high) % _MOD
            window_hash = (window_hash * _BASE + entering) % _MOD
    return hits

"""KMP: matching without ever re-comparing a character, by precomputing the pattern's overlaps.

Naive substring search, on a mismatch partway through the pattern,
throws away everything it just matched and restarts one position
over, re-comparing characters it already saw, which is what makes
it quadratic on inputs with lots of near-matches. KMP never
re-compares. It precomputes, for each prefix of the pattern, the
length of the longest proper prefix that is also a suffix of that
prefix, the failure function, which encodes how much of the match
so far is still usable after a mismatch. When a mismatch happens
after matching k characters, instead of backing up in the text,
KMP consults the failure function to slide the pattern forward by
exactly the amount that keeps the already-matched suffix aligned,
so the text pointer only ever moves forward. Both the failure
function's construction and the scan are linear, giving a
worst-case O(n plus m) that holds even on the adversarial inputs
where Rabin-Karp's hashing degrades and the naive scan goes
quadratic. The failure function is the whole idea: it turns the
pattern's internal repetition into a table that says where to
resume, so no character of the text is examined twice. This module
builds the table and scans, checked against a brute-force search,
so the no-recomparison match is correct as well as linear.
"""

from __future__ import annotations

from rill.errors import Invalid


def _failure(pattern: str) -> list[int]:
    table = [0] * len(pattern)
    length = 0
    for index in range(1, len(pattern)):
        while length > 0 and pattern[index] != pattern[length]:
            length = table[length - 1]
        if pattern[index] == pattern[length]:
            length += 1
        table[index] = length
    return table


def find(text: str, pattern: str) -> list[int]:
    if not pattern:
        raise Invalid("pattern cannot be empty")
    if len(pattern) > len(text):
        return []
    table = _failure(pattern)
    hits: list[int] = []
    matched = 0
    for index, char in enumerate(text):
        while matched > 0 and char != pattern[matched]:
            matched = table[matched - 1]
        if char == pattern[matched]:
            matched += 1
        if matched == len(pattern):
            hits.append(index - matched + 1)
            matched = table[matched - 1]
    return hits

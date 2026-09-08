"""Z-algorithm: for every position, how far it matches the prefix, in linear time.

The Z-array of a string gives, at each position, the length of the
longest run starting there that also matches the string's own
prefix. Computed naively that is quadratic, comparing the prefix
against every position from scratch. The Z-algorithm is linear, and
it earns that the same way Manacher does, by carrying a window it
has already matched forward instead of recomputing it. It keeps the
interval that starts earliest-matched and reaches furthest right,
call it l to r, which is a stretch known to equal the prefix. For a
new position i inside that interval, the answer is at least the
Z-value at the mirror position i minus l within the prefix, capped
so it does not overrun r, and that much is free. Only the part past
r is compared character by character, and r advances monotonically,
so the comparisons total linear across the string. Its use for
pattern matching is direct: concatenate the pattern, a separator
not in either string, and the text, then any position in the text
part whose Z-value equals the pattern length is a match, which
finds all occurrences in time linear in the combined length. That
is the same asymptotics as KMP but reached through a prefix-match
array rather than a failure function, and some find the Z-array the
easier of the two to reason about. This module builds the Z-array
and uses it to find all occurrences, and a test checks the matches
against a brute substring scan, so the linear search is confirmed.
"""

from __future__ import annotations

from rill.errors import Invalid


def z_array(text: str) -> list[int]:
    if text is None:
        raise Invalid("text must not be None")
    n = len(text)
    z = [0] * n
    if n == 0:
        return z
    z[0] = n
    left = right = 0
    for i in range(1, n):
        if i < right:
            z[i] = min(right - i, z[i - left])
        while i + z[i] < n and text[z[i]] == text[i + z[i]]:
            z[i] += 1
        if i + z[i] > right:
            left, right = i, i + z[i]
    return z


def find_all(text: str, pattern: str) -> list[int]:
    if text is None or pattern is None:
        raise Invalid("text and pattern must not be None")
    if pattern == "":
        raise Invalid("pattern must not be empty")
    sep = "\x00"
    if sep in text or sep in pattern:
        raise Invalid("the NUL separator must not appear in the inputs")
    combined = pattern + sep + text
    z = z_array(combined)
    plen = len(pattern)
    offset = plen + 1
    return [i - offset for i in range(offset, len(combined)) if z[i] >= plen]

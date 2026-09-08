"""Booth's algorithm: the lexicographically least rotation of a string, in linear time.

A string has as many rotations as it has characters, each formed by
cutting at some position and moving the front to the back. Among
them one is lexicographically smallest, and it is a useful canonical
form: two strings are rotations of each other exactly when their
least rotations are equal, so reducing to the least rotation lets a
necklace, a cyclic sequence with no fixed start, be compared and
hashed by content regardless of where it was cut. The obvious way is
to generate all n rotations and take the minimum, which is quadratic,
n rotations each of length n to compare. Booth's algorithm finds the
starting index of the least rotation in linear time using a modified
failure function over the string doubled conceptually. It scans with
two candidate starts and a match length, and when a mismatch shows
one candidate leads to a smaller rotation, it advances the losing
candidate past the region already known to be no better, so no
position is examined more than a constant number of times. The
output is an index into the original string; the least rotation is
the string read cyclically from there. The finding worth stating is
that the doubled-string failure function collapses the quadratic
all-rotations comparison into a linear scan, the same shape of win
KMP and Z bring to matching. This module returns the least rotation
and its index, and a test compares them against the brute minimum
over all rotations, so the linear scan is confirmed to find the true
least rotation.
"""

from __future__ import annotations

from rill.errors import Invalid


def least_rotation_index(text: str) -> int:
    if text is None:
        raise Invalid("text must not be None")
    if text == "":
        return 0
    s = text + text
    n = len(s)
    failure = [-1] * n
    k = 0
    for j in range(1, n):
        sj = s[j]
        i = failure[j - k - 1]
        while i != -1 and sj != s[k + i + 1]:
            if sj < s[k + i + 1]:
                k = j - i - 1
            i = failure[i]
        if sj != s[k + i + 1]:
            if sj < s[k]:
                k = j
            failure[j - k] = -1
        else:
            failure[j - k] = i + 1
    return k % len(text)


def least_rotation(text: str) -> str:
    if text is None:
        raise Invalid("text must not be None")
    if text == "":
        return ""
    idx = least_rotation_index(text)
    return text[idx:] + text[:idx]

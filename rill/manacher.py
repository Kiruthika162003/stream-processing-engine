"""Manacher: the longest palindromic substring in linear rather than quadratic time.

The direct way to find the longest palindrome is to expand around
each center, both the n single-character centers and the n-1 gaps
between characters, comparing outward until the two sides differ.
That is quadratic, because a long palindrome makes each expansion
long and there are linearly many centers. Manacher's method is
linear, and it gets there by never re-comparing a pair of
characters it has already matched from a wider palindrome. It works
on a transformed string with a separator inserted between every
pair of characters and at both ends, so that every palindrome,
odd or even length in the original, becomes odd length and centered
on a real position, which removes the odd-even split. It then walks
the centers left to right keeping the palindrome that reaches
furthest right seen so far, its center c and right edge r. For a
new center i inside that reach, the palindrome around i is at least
as wide as the one around i's mirror across c, capped so it does
not run past r, and that lower bound is free, no comparisons. Only
the part beyond r is checked character by character, and since r
never moves backward, the total checking is linear across the whole
walk. The distinguishing claim, the reason to prefer it, is that
the mirror lower bound turns the quadratic expansion into a linear
one without giving up correctness. This module returns the longest
palindromic substring, and a test compares it against the brute
expand-around-center answer on random strings, so the linear method
is confirmed to agree with the obvious one.
"""

from __future__ import annotations

from rill.errors import Invalid


def longest_palindrome(text: str) -> str:
    if text is None:
        raise Invalid("text must not be None")
    if text == "":
        return ""
    # sentinel-free transform: ^ # a # b # a # $ has odd length and real centers
    t = "^#" + "#".join(text) + "#$"
    n = len(t)
    radius = [0] * n
    center = right = 0
    for i in range(1, n - 1):
        if i < right:
            radius[i] = min(right - i, radius[2 * center - i])
        while t[i + radius[i] + 1] == t[i - radius[i] - 1]:
            radius[i] += 1
        if i + radius[i] > right:
            center, right = i, i + radius[i]
    best_len = max(radius)
    best_center = radius.index(best_len)
    start = (best_center - best_len) // 2
    return text[start : start + best_len]

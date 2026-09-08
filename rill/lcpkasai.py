"""Kasai's LCP array: longest common prefixes of adjacent suffixes, in linear time.

The suffix array orders the suffixes; the LCP array records, for each
adjacent pair in that order, how many leading characters they share.
Together they answer questions the suffix array alone cannot: the
longest repeated substring is the deepest LCP entry, since two
suffixes sharing a long prefix means that prefix appears at both
their start positions, and the number of distinct substrings is the
total substring count minus the sum of the LCP array, because each
LCP entry counts prefixes already seen at the previous suffix.
Computing the LCP naively, comparing each adjacent pair character by
character, is quadratic. Kasai's algorithm is linear, and it rests on
one non-obvious monotonicity. Process the suffixes not in sorted
order but in position order, from the suffix starting at zero onward.
When moving from the suffix at position i to the one at position i
plus one, that is dropping the first character, the length of its
common prefix with its neighbor in sorted order can fall by at most
one from the previous suffix's value. So the running match length is
decremented by one at each step and then only extended, never rebuilt
from zero, and since it is bounded by the string length and only
decremented once per position, the total character comparisons are
linear. The finding worth stating is that the drop-by-at-most-one
property is the whole reason the array builds in linear rather than
quadratic time, and it depends on visiting suffixes in position order
against the rank array, not in sorted order. This module builds the
LCP array with Kasai and reads the longest repeated substring from
it, and a test checks both against brute computations, so the
linear build is confirmed.
"""

from __future__ import annotations

from rill.errors import Invalid
from rill.suffixarray import suffix_array


def lcp_array(text: str, sa: list[int]) -> list[int]:
    if text is None or sa is None:
        raise Invalid("text and suffix array must not be None")
    n = len(text)
    if n == 0:
        return []
    rank = [0] * n
    for i, s in enumerate(sa):
        rank[s] = i
    lcp = [0] * n
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]
            while i + h < n and j + h < n and text[i + h] == text[j + h]:
                h += 1
            lcp[rank[i]] = h
            if h > 0:
                h -= 1
        else:
            h = 0
    return lcp


def longest_repeated_substring(text: str) -> str:
    if text is None:
        raise Invalid("text must not be None")
    if text == "":
        return ""
    sa = suffix_array(text)
    lcp = lcp_array(text, sa)
    best_len = max(lcp)
    if best_len == 0:
        return ""
    at = lcp.index(best_len)
    start = sa[at]
    return text[start : start + best_len]

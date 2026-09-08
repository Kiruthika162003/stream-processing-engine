from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.lcpkasai import lcp_array, longest_repeated_substring
from rill.suffixarray import suffix_array


def _brute_lcp(s, sa):
    n = len(s)
    res = [0] * n
    for k in range(1, n):
        a, b = s[sa[k - 1] :], s[sa[k] :]
        m = 0
        while m < len(a) and m < len(b) and a[m] == b[m]:
            m += 1
        res[k] = m
    return res


def _brute_lrs(s):
    best = ""
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            m = 0
            while j + m < len(s) and s[i + m] == s[j + m]:
                m += 1
            if m > len(best):
                best = s[i : i + m]
    return best


class TestLcp:
    def test_the_banana_lcp(self):
        assert lcp_array("banana", suffix_array("banana")) == [0, 1, 3, 0, 0, 2]

    def test_it_matches_a_brute_lcp(self):
        rng = random.Random(61)
        for _ in range(4000):
            s = "".join(rng.choice("ab") for _ in range(rng.randint(1, 16)))
            sa = suffix_array(s)
            assert lcp_array(s, sa) == _brute_lcp(s, sa)

    def test_empty(self):
        assert lcp_array("", []) == []


class TestLongestRepeated:
    def test_known_cases(self):
        assert longest_repeated_substring("banana") == "ana"
        assert longest_repeated_substring("abcabcabc") == "abcabc"

    def test_no_repeat_is_empty(self):
        assert longest_repeated_substring("abcde") == ""

    def test_it_matches_brute_in_length(self):
        rng = random.Random(62)
        for _ in range(3000):
            s = "".join(rng.choice("ab") for _ in range(rng.randint(1, 16)))
            assert len(longest_repeated_substring(s)) == len(_brute_lrs(s))


class TestRefusals:
    def test_none_lcp_is_refused(self):
        with pytest.raises(Invalid):
            lcp_array(None, [])

    def test_none_lrs_is_refused(self):
        with pytest.raises(Invalid):
            longest_repeated_substring(None)

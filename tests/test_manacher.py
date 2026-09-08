from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.manacher import longest_palindrome


def _brute(s: str) -> str:
    best = ""
    for i in range(len(s)):
        for start, stop in ((i, i), (i, i + 1)):
            a, b = start, stop
            while a >= 0 and b < len(s) and s[a] == s[b]:
                a -= 1
                b += 1
            cand = s[a + 1 : b]
            if len(cand) > len(best):
                best = cand
    return best


class TestKnownCases:
    def test_odd_length_palindrome(self):
        assert longest_palindrome("babad") in {"bab", "aba"}

    def test_even_length_palindrome(self):
        assert longest_palindrome("cbbd") == "bb"

    def test_a_long_embedded_palindrome(self):
        assert longest_palindrome("forgeeksskeegfor") == "geeksskeeg"

    def test_the_whole_string_is_a_palindrome(self):
        assert longest_palindrome("racecar") == "racecar"


class TestAgainstBrute:
    def test_it_agrees_in_length_with_expand_around_center(self):
        rng = random.Random(11)
        for _ in range(5000):
            s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 12)))
            got = longest_palindrome(s)
            # the returned slice is itself a palindrome
            assert got == got[::-1]
            # and it is as long as the brute-force answer
            assert len(got) == len(_brute(s))


class TestEdges:
    def test_empty_and_single(self):
        assert longest_palindrome("") == ""
        assert longest_palindrome("z") == "z"

    def test_no_repeat_returns_one_character(self):
        assert len(longest_palindrome("abcde")) == 1


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            longest_palindrome(None)

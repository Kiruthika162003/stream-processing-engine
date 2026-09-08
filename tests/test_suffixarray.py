from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.suffixarray import search, suffix_array


class TestConstruction:
    def test_the_classic_banana(self):
        assert suffix_array("banana") == [5, 3, 1, 0, 4, 2]

    def test_it_matches_brute_sorted_suffixes(self):
        rng = random.Random(59)
        for _ in range(4000):
            s = "".join(rng.choice("ab") for _ in range(rng.randint(1, 18)))
            brute = sorted(range(len(s)), key=lambda i, s=s: s[i:])
            assert suffix_array(s) == brute

    def test_empty_and_single(self):
        assert suffix_array("") == []
        assert suffix_array("z") == [0]


class TestSearch:
    def test_overlapping_matches(self):
        sa = suffix_array("banana")
        assert search("banana", "ana", sa) == [1, 3]

    def test_absent_pattern(self):
        sa = suffix_array("banana")
        assert search("banana", "xyz", sa) == []

    def test_it_agrees_with_a_scan(self):
        rng = random.Random(60)
        for _ in range(3000):
            s = "".join(rng.choice("ab") for _ in range(rng.randint(1, 18)))
            sa = suffix_array(s)
            p = "".join(rng.choice("ab") for _ in range(rng.randint(1, 3)))
            expected = sorted(
                i for i in range(len(s)) if s[i : i + len(p)] == p
            )
            assert search(s, p, sa) == expected


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            suffix_array(None)

    def test_an_empty_pattern_is_refused(self):
        with pytest.raises(Invalid):
            search("abc", "", suffix_array("abc"))

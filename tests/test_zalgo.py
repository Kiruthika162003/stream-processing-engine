from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.zalgo import find_all, z_array


class TestZArray:
    def test_the_first_entry_is_the_whole_length(self):
        assert z_array("abcabc")[0] == 6

    def test_a_known_array(self):
        assert z_array("aabxaabxcaabxaabxay") == [
            19, 1, 0, 0, 4, 1, 0, 0, 0, 8, 1, 0, 0, 5, 1, 0, 0, 1, 0,
        ]

    def test_empty_is_empty(self):
        assert z_array("") == []


class TestFindAll:
    def test_overlapping_matches_are_all_found(self):
        assert find_all("banana", "ana") == [1, 3]

    def test_a_pattern_absent_gives_no_matches(self):
        assert find_all("abcabc", "xyz") == []

    def test_it_agrees_with_a_brute_substring_scan(self):
        rng = random.Random(13)
        for _ in range(5000):
            text = "".join(rng.choice("ab") for _ in range(rng.randint(0, 20)))
            pattern = "".join(rng.choice("ab") for _ in range(rng.randint(1, 4)))
            brute = [
                i for i in range(len(text) - len(pattern) + 1)
                if text[i : i + len(pattern)] == pattern
            ]
            assert find_all(text, pattern) == brute


class TestRefusals:
    def test_none_text_is_refused(self):
        with pytest.raises(Invalid):
            z_array(None)

    def test_an_empty_pattern_is_refused(self):
        with pytest.raises(Invalid):
            find_all("abc", "")

    def test_a_nul_in_the_input_is_refused(self):
        with pytest.raises(Invalid):
            find_all("ab\x00c", "b")

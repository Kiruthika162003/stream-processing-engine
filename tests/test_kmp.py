from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.kmp import _failure, find


def _brute(text: str, pattern: str) -> list[int]:
    return [
        i for i in range(len(text) - len(pattern) + 1) if text[i:].startswith(pattern)
    ]


class TestCorrectness:
    def test_it_matches_brute_force_over_random_text(self):
        rng = random.Random(3)
        for _ in range(500):
            text = "".join(rng.choice("ab") for _ in range(rng.randint(1, 30)))
            pattern = "".join(rng.choice("ab") for _ in range(rng.randint(1, 5)))
            assert find(text, pattern) == _brute(text, pattern)

    def test_it_finds_overlapping_occurrences(self):
        assert find("aaaa", "aa") == [0, 1, 2]


class TestFailureFunction:
    def test_the_failure_function_encodes_prefix_suffix_overlap(self):
        assert _failure("ababab") == [0, 0, 1, 2, 3, 4]

    def test_no_overlap_is_all_zeros(self):
        assert _failure("abcd") == [0, 0, 0, 0]


class TestEdges:
    def test_no_occurrence_returns_empty(self):
        assert find("abcabc", "xyz") == []

    def test_a_pattern_longer_than_the_text_returns_empty(self):
        assert find("ab", "abc") == []


class TestRefusals:
    def test_an_empty_pattern_is_refused(self):
        with pytest.raises(Invalid):
            find("text", "")

from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.longestunique import longest_unique, longest_unique_or_refuse


def _brute(sequence: str) -> int:
    best = 0
    for i in range(len(sequence)):
        seen: set[str] = set()
        for j in range(i, len(sequence)):
            if sequence[j] in seen:
                break
            seen.add(sequence[j])
            best = max(best, j - i + 1)
    return best


class TestCorrectness:
    def test_the_classic_cases(self):
        assert longest_unique("abcabcbb") == 3
        assert longest_unique("bbbbb") == 1
        assert longest_unique("pwwkew") == 3

    def test_it_matches_brute_force(self):
        rng = random.Random(5)
        for _ in range(500):
            sequence = "".join(rng.choice("abc") for _ in range(rng.randint(0, 25)))
            assert longest_unique(sequence) == _brute(sequence)


class TestEdges:
    def test_all_distinct_is_the_whole_length(self):
        assert longest_unique("abcd") == 4

    def test_empty_is_zero(self):
        assert longest_unique("") == 0


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            longest_unique_or_refuse(None)

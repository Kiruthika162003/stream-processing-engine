from __future__ import annotations

import random
import string

import pytest

from rill.errors import Invalid
from rill.horspool import HorspoolSearch


def _brute(text: str, pattern: str) -> list[int]:
    return [
        i for i in range(len(text) - len(pattern) + 1) if text[i:].startswith(pattern)
    ]


class TestCorrectness:
    def test_it_matches_brute_force_over_random_text(self):
        rng = random.Random(4)
        for _ in range(500):
            length = rng.randint(1, 40)
            text = "".join(rng.choice(string.ascii_lowercase) for _ in range(length))
            pattern = "".join(
                rng.choice(string.ascii_lowercase) for _ in range(rng.randint(1, 5))
            )
            assert HorspoolSearch(pattern).find(text) == _brute(text, pattern)

    def test_it_finds_all_positions(self):
        assert HorspoolSearch("ab").find("ababab") == [0, 2, 4]


class TestSublinear:
    def test_it_examines_fewer_than_the_text_length(self):
        text = "abcdefghij" * 100  # 1000 chars, pattern absent
        search = HorspoolSearch("xyz")
        search.find(text)
        assert search.comparisons() < len(text)
        assert search.comparisons() < 400  # skips by the pattern length


class TestEdges:
    def test_a_pattern_longer_than_the_text_finds_nothing(self):
        assert HorspoolSearch("abc").find("ab") == []


class TestRefusals:
    def test_an_empty_pattern_is_refused(self):
        with pytest.raises(Invalid):
            HorspoolSearch("")

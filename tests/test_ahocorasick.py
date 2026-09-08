from __future__ import annotations

import random

import pytest

from rill.ahocorasick import AhoCorasick
from rill.errors import Invalid


def _brute(text: str, patterns: list[str]) -> list[tuple[int, str]]:
    out = []
    for pattern in patterns:
        for i in range(len(text) - len(pattern) + 1):
            if text[i:].startswith(pattern):
                out.append((i, pattern))
    return sorted(out)


class TestCorrectness:
    def test_it_matches_brute_force_over_random_inputs(self):
        rng = random.Random(5)
        for _ in range(300):
            patterns = list(
                {
                    "".join(rng.choice("ab") for _ in range(rng.randint(1, 4)))
                    for _ in range(rng.randint(1, 5))
                }
            )
            text = "".join(rng.choice("ab") for _ in range(rng.randint(1, 30)))
            assert sorted(AhoCorasick(patterns).find_all(text)) == _brute(
                text, patterns
            )

    def test_the_classic_dictionary(self):
        auto = AhoCorasick(["he", "she", "his", "hers"])
        assert sorted(auto.find_all("ushers")) == [
            (1, "she"),
            (2, "he"),
            (2, "hers"),
        ]

    def test_a_suffix_pattern_is_found_at_the_same_position(self):
        # "he" is a suffix of "she"; both end where she ends
        auto = AhoCorasick(["she", "he"])
        matches = auto.find_all("she")
        assert (0, "she") in matches
        assert (1, "he") in matches


class TestRefusals:
    def test_no_patterns_is_refused(self):
        with pytest.raises(Invalid):
            AhoCorasick([])

    def test_an_empty_pattern_is_refused(self):
        with pytest.raises(Invalid):
            AhoCorasick(["a", ""])

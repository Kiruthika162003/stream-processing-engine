from __future__ import annotations

import random

import pytest

from rill.booth import least_rotation, least_rotation_index
from rill.errors import Invalid


def _brute(s: str) -> str:
    if s == "":
        return ""
    return min(s[i:] + s[:i] for i in range(len(s)))


class TestLeastRotation:
    def test_a_concrete_rotation(self):
        assert least_rotation("bbaaccaadd") == "aaccaaddbb"

    def test_it_matches_the_brute_minimum(self):
        rng = random.Random(41)
        for _ in range(20000):
            s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 12)))
            assert least_rotation(s) == _brute(s)

    def test_rotations_of_each_other_share_a_least_rotation(self):
        assert least_rotation("abcde") == least_rotation("cdeab")
        assert least_rotation("abcde") == least_rotation("eabcd")

    def test_an_already_minimal_string_stays(self):
        assert least_rotation_index("aab") == 0
        assert least_rotation("aab") == "aab"


class TestEdges:
    def test_empty_and_single(self):
        assert least_rotation("") == ""
        assert least_rotation("z") == "z"
        assert least_rotation_index("") == 0

    def test_all_equal_characters(self):
        assert least_rotation("aaaa") == "aaaa"


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            least_rotation(None)

    def test_none_index_is_refused(self):
        with pytest.raises(Invalid):
            least_rotation_index(None)

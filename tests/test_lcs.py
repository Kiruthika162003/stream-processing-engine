from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.lcs import lcs, lcs_length


def _is_subsequence(candidate: list[str], sequence: list[str]) -> bool:
    iterator = iter(sequence)
    return all(item in iterator for item in candidate)


class TestLength:
    def test_the_classic_example(self):
        left = list("ABCBDAB")
        right = list("BDCAB")
        assert lcs_length(left, right) == 4

    def test_disjoint_sequences_share_nothing(self):
        assert lcs_length(list("abc"), list("xyz")) == 0

    def test_identical_sequences_share_everything(self):
        assert lcs_length(list("abc"), list("abc")) == 3

    def test_an_empty_sequence_shares_nothing(self):
        assert lcs_length([], list("abc")) == 0


class TestAlignment:
    def test_the_result_is_a_subsequence_of_both(self):
        rng = random.Random(1)
        for _ in range(300):
            left = [rng.choice("abc") for _ in range(rng.randint(0, 10))]
            right = [rng.choice("abc") for _ in range(rng.randint(0, 10))]
            result = lcs(left, right)
            assert _is_subsequence(result, left)
            assert _is_subsequence(result, right)


class TestRefusals:
    def test_a_none_sequence_is_refused(self):
        with pytest.raises(Invalid):
            lcs(None, list("abc"))

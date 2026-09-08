from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.rle import decode, encode, run_count

SORTED = ["a"] * 400 + ["b"] * 400 + ["c"] * 200


class TestOrderingDrivesCompression:
    def test_a_sorted_column_collapses_to_a_few_runs(self):
        assert run_count(SORTED) == 3

    def test_shuffling_the_same_values_explodes_the_runs(self):
        rng = random.Random(1)
        shuffled = SORTED[:]
        rng.shuffle(shuffled)
        assert run_count(shuffled) > 500


class TestRoundTrip:
    def test_encode_then_decode_is_the_identity(self):
        assert decode(encode(SORTED)) == SORTED

    def test_encoding_names_the_value_and_the_length(self):
        assert encode(["x", "x", "y"]) == [("x", 2), ("y", 1)]


class TestRefusals:
    def test_encoding_nothing_is_refused(self):
        with pytest.raises(Invalid):
            encode([])

    def test_a_nonpositive_run_length_is_refused(self):
        with pytest.raises(Invalid):
            decode([("x", 0)])

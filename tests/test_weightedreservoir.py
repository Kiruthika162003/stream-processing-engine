from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.weightedreservoir import weighted_sample


class TestWeightProportional:
    def test_inclusion_frequency_tracks_the_weight_ratio(self):
        rng = random.Random(3)
        items = [("a", 1), ("b", 3)]
        picks = {"a": 0, "b": 0}
        trials = 6000
        for _ in range(trials):
            chosen = weighted_sample(items, 1, rng.random)
            picks[chosen[0]] += 1
        # b weighs three times a, so it is picked about three times as often
        assert 2.7 < picks["b"] / picks["a"] < 3.3
        assert picks["a"] + picks["b"] == trials


class TestMechanics:
    def test_the_sample_holds_exactly_k_items(self):
        rng = random.Random(1)
        items = [(f"i{n}", n + 1) for n in range(10)]
        assert len(weighted_sample(items, 4, rng.random)) == 4

    def test_size_at_least_the_stream_keeps_everything(self):
        rng = random.Random(1)
        items = [("a", 1), ("b", 1)]
        assert weighted_sample(items, 5, rng.random) == ["a", "b"]


class TestRefusals:
    def test_a_nonpositive_size_is_refused(self):
        with pytest.raises(Invalid):
            weighted_sample([("a", 1)], 0, random.Random(1).random)

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            weighted_sample([("a", 0)], 1, random.Random(1).random)

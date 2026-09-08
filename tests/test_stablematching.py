from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.stablematching import stable_matching


def _is_stable(match, proposer_prefs, receiver_prefs) -> bool:
    prank = {p: {r: i for i, r in enumerate(o)} for p, o in proposer_prefs.items()}
    rrank = {r: {p: i for i, p in enumerate(o)} for r, o in receiver_prefs.items()}
    inverse = {r: p for p, r in match.items()}
    for proposer in proposer_prefs:
        for receiver in proposer_prefs[proposer]:
            if prank[proposer][receiver] < prank[proposer][match[proposer]] and (
                rrank[receiver][proposer] < rrank[receiver][inverse[receiver]]
            ):
                return False
    return True


class TestStability:
    def test_the_classic_instance_is_stable(self):
        proposer = {"a": ["X", "Y", "Z"], "b": ["Y", "X", "Z"], "c": ["X", "Y", "Z"]}
        receiver = {"X": ["b", "a", "c"], "Y": ["a", "b", "c"], "Z": ["a", "b", "c"]}
        match = stable_matching(proposer, receiver)
        assert len(match) == 3
        assert _is_stable(match, proposer, receiver)

    def test_every_matching_is_stable_over_random_instances(self):
        rng = random.Random(3)
        for _ in range(300):
            size = rng.randint(1, 5)
            proposers = [f"p{i}" for i in range(size)]
            receivers = [f"r{i}" for i in range(size)]
            proposer = {p: rng.sample(receivers, size) for p in proposers}
            receiver = {r: rng.sample(proposers, size) for r in receivers}
            match = stable_matching(proposer, receiver)
            assert len(match) == size
            assert _is_stable(match, proposer, receiver)


class TestRefusals:
    def test_mismatched_sizes_are_refused(self):
        with pytest.raises(Invalid):
            stable_matching({"a": ["X"]}, {"X": ["a"], "Y": ["a"]})

    def test_an_unknown_receiver_is_refused(self):
        with pytest.raises(Invalid):
            stable_matching({"a": ["Z"]}, {"X": ["a"]})

from __future__ import annotations

import random
from collections import Counter

import pytest

from rill.errors import Invalid
from rill.misragries import MisraGries


class TestNoFalseNegatives:
    def test_every_true_heavy_hitter_survives(self):
        rng = random.Random(2)
        for _ in range(50):
            k = rng.randint(2, 6)
            length = rng.randint(50, 500)
            stream = [str(rng.randrange(20)) for _ in range(length)]
            gries = MisraGries(k=k)
            for item in stream:
                gries.observe(item)
            true = Counter(stream)
            heavy = {item for item, count in true.items() if count > length / k}
            # no true heavy hitter is missed
            assert heavy <= gries.candidates()

    def test_a_clear_heavy_hitter_is_a_candidate(self):
        gries = MisraGries(k=4)
        for _ in range(400):
            gries.observe("hot")
        for number in range(600):
            gries.observe(f"n{number % 200}")
        assert "hot" in gries.candidates()


class TestBounded:
    def test_the_candidate_set_is_at_most_k_minus_one(self):
        gries = MisraGries(k=3)
        for number in range(100):
            gries.observe(str(number))
        assert len(gries.candidates()) <= 2


class TestRefusals:
    def test_a_k_below_two_is_refused(self):
        with pytest.raises(Invalid):
            MisraGries(k=1)

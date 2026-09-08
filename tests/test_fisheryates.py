from __future__ import annotations

import random
import statistics
from collections import Counter

import pytest

from rill.errors import Invalid
from rill.fisheryates import naive_shuffle, shuffle


def _distribution(fn, seed: int) -> Counter:
    rng = random.Random(seed)

    def pick(hi: int) -> int:
        return rng.randint(0, hi)

    counts: Counter = Counter()
    for _ in range(60000):
        counts[tuple(fn(["a", "b", "c"], pick))] += 1
    return counts


class TestUniformity:
    def test_fisher_yates_is_near_uniform(self):
        counts = _distribution(shuffle, seed=1)
        assert len(counts) == 6  # all permutations of three
        assert max(counts.values()) / min(counts.values()) < 1.1

    def test_the_naive_variant_is_biased(self):
        counts = _distribution(naive_shuffle, seed=1)
        assert max(counts.values()) / min(counts.values()) > 1.2

    def test_fisher_yates_spread_is_far_tighter(self):
        fy = statistics.pstdev(_distribution(shuffle, seed=1).values())
        naive = statistics.pstdev(_distribution(naive_shuffle, seed=1).values())
        assert fy < naive / 5


class TestMechanics:
    def test_it_returns_a_permutation_of_the_input(self):
        rng = random.Random(2)
        result = shuffle(["a", "b", "c", "d"], lambda hi: rng.randint(0, hi))
        assert sorted(result) == ["a", "b", "c", "d"]

    def test_it_does_not_mutate_the_input(self):
        items = ["a", "b", "c"]
        shuffle(items, lambda _i: 0)
        assert items == ["a", "b", "c"]


class TestRefusals:
    def test_a_picker_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            shuffle(["a", "b"], lambda i: i + 5)

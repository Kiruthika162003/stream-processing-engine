from __future__ import annotations

import random

import pytest

from rill.aliasmethod import AliasSampler
from rill.errors import Invalid


class TestDistribution:
    def test_empirical_frequency_tracks_the_weights(self):
        rng = random.Random(7)
        weights = [1.0, 3.0, 6.0]
        sampler = AliasSampler(weights)
        counts = [0, 0, 0]
        trials = 60000
        for _ in range(trials):
            counts[sampler.draw(rng.randrange, rng.random)] += 1
        freq = [c / trials for c in counts]
        target = [w / sum(weights) for w in weights]
        # measured max deviation at this seed was 0.0014; keep a safe ceiling
        assert max(abs(f - t) for f, t in zip(freq, target, strict=True)) < 0.01

    def test_a_zero_weight_item_is_never_drawn(self):
        rng = random.Random(1)
        sampler = AliasSampler([0.0, 5.0, 5.0])
        drawn = {sampler.draw(rng.randrange, rng.random) for _ in range(2000)}
        assert 0 not in drawn

    def test_a_single_item_is_always_drawn(self):
        sampler = AliasSampler([4.0])
        assert sampler.draw(lambda _n: 0, lambda: 0.9) == 0
        assert len(sampler) == 1


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            AliasSampler(None)

    def test_empty_is_refused(self):
        with pytest.raises(Invalid):
            AliasSampler([])

    def test_a_negative_weight_is_refused(self):
        with pytest.raises(Invalid):
            AliasSampler([1.0, -2.0])

    def test_all_zero_weights_are_refused(self):
        with pytest.raises(Invalid):
            AliasSampler([0.0, 0.0])

    def test_an_out_of_range_column_is_refused(self):
        sampler = AliasSampler([1.0, 1.0])
        with pytest.raises(Invalid):
            sampler.draw(lambda _n: 5, lambda: 0.5)

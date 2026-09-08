from __future__ import annotations

import random

import pytest

from rill.countsketch import CountSketch
from rill.errors import Invalid


class TestExactWithoutCollision:
    def test_a_lone_key_reads_back_exactly(self):
        sketch = CountSketch(depth=5, width=64)
        sketch.update("only", 7)
        assert sketch.estimate("only") == 7

    def test_an_unseen_key_reads_near_zero(self):
        sketch = CountSketch(depth=5, width=64)
        sketch.update("a", 3)
        assert sketch.estimate("unseen") == 0


class TestHeavyHitterAccuracy:
    def test_a_heavy_hitter_estimates_close_under_noise(self):
        rng = random.Random(8)
        sketch = CountSketch(depth=5, width=64)
        sketch.update("hot", 1000)
        for _ in range(2000):
            sketch.update(f"noise-{rng.randrange(500)}", 1)
        estimate = sketch.estimate("hot")
        # unbiased: close on either side, unlike count-min's one-sided inflation
        assert abs(estimate - 1000) <= 20


class TestRefusals:
    def test_a_nonpositive_dimension_is_refused(self):
        with pytest.raises(Invalid):
            CountSketch(depth=0, width=10)

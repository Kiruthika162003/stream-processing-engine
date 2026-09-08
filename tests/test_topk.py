from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.topk import SpaceSaving


def skewed_sketch() -> SpaceSaving:
    sketch = SpaceSaving(capacity=3)
    for _ in range(50):
        sketch.offer("bieber")
    for _ in range(30):
        sketch.offer("ronaldo")
    for number in range(20):
        sketch.offer(f"quiet-{number}")
    return sketch


class TestTheBargain:
    def test_known_keys_count_exactly(self):
        sketch = SpaceSaving(capacity=3)
        for _ in range(5):
            sketch.offer("a")
        assert sketch.counts["a"] == 5
        assert sketch.overcounts["a"] == 0

    def test_the_stranger_inherits_the_victims_count(self):
        sketch = SpaceSaving(capacity=2)
        sketch.offer("a")
        sketch.offer("b")
        sketch.offer("b")
        sketch.offer("c")
        assert sketch.counts["c"] == 2
        assert sketch.overcounts["c"] == 1
        assert "a" not in sketch.counts

    def test_a_counterless_sketch_is_refused(self):
        with pytest.raises(Invalid):
            SpaceSaving(capacity=0)


class TestTheFamous:
    def test_the_truly_heavy_are_never_missed(self):
        sketch = skewed_sketch()
        top = sketch.hitters(top=2)
        assert top[0].startswith("bieber: 50")
        assert top[1].startswith("ronaldo: 30")

    def test_every_hitter_carries_its_error_bar(self):
        for line in skewed_sketch().hitters(top=3):
            assert "overcount at most" in line

    def test_the_famous_keys_have_zero_overcount(self):
        sketch = skewed_sketch()
        assert sketch.overcounts["bieber"] == 0
        assert sketch.overcounts["ronaldo"] == 0

    def test_the_reading_guide_states_the_honest_guarantee(self):
        guide = skewed_sketch().reading_guide()
        assert "never misses a heavy hitter" in guide
        assert "flatters a light one" in guide

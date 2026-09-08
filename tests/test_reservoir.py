from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.reservoir import Reservoir


class TestMechanics:
    def test_the_first_k_fill_the_reservoir(self):
        res = Reservoir(size=3, pick=lambda _seen: 0)
        for item in ("a", "b", "c"):
            res.observe(item)
        assert res.sample() == ["a", "b", "c"]

    def test_a_picker_that_hits_a_slot_replaces_it(self):
        res = Reservoir(size=1, pick=lambda _seen: 0)
        res.observe("first")
        res.observe("second")
        assert res.sample() == ["second"]

    def test_a_picker_that_misses_keeps_the_member(self):
        res = Reservoir(size=1, pick=lambda seen: seen)
        res.observe("first")
        res.observe("second")
        assert res.sample() == ["first"]

    def test_a_picker_out_of_range_is_refused(self):
        res = Reservoir(size=1, pick=lambda seen: seen + 5)
        res.observe("first")
        with pytest.raises(Invalid):
            res.observe("second")


class TestUniformity:
    def test_late_events_are_sampled_as_often_as_early_ones(self):
        rng = random.Random(11)
        length, trials = 100, 3000
        counts = [0] * length
        for _ in range(trials):
            res = Reservoir(size=1, pick=lambda seen: rng.randint(0, seen))
            for tick in range(length):
                res.observe(str(tick))
            counts[int(res.sample()[0])] += 1
        # uniform would give 30 per index; keeping the first k would
        # pile all 3000 on index 0 and leave the last index at zero.
        assert min(counts) >= 10
        assert max(counts) <= 60
        assert counts[-1] > 15


class TestRefusals:
    def test_a_nonpositive_size_is_refused(self):
        with pytest.raises(Invalid):
            Reservoir(size=0, pick=lambda _seen: 0)

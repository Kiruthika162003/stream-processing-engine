from __future__ import annotations

from collections import Counter

import pytest

from rill.errors import Invalid
from rill.smoothwrr import SmoothWeightedRoundRobin


def _max_run(sequence: list[str], value: str) -> int:
    best = current = 0
    for item in sequence:
        current = current + 1 if item == value else 0
        best = max(best, current)
    return best


class TestRatio:
    def test_a_cycle_hits_each_server_its_weight_of_times(self):
        wrr = SmoothWeightedRoundRobin(weights={"a": 5, "b": 1, "c": 1})
        counts = Counter(wrr.cycle())
        assert counts == {"a": 5, "b": 1, "c": 1}


class TestSmoothness:
    def test_the_heavy_server_does_not_burst_its_whole_weight(self):
        wrr = SmoothWeightedRoundRobin(weights={"a": 5, "b": 1, "c": 1})
        sequence = wrr.cycle()
        assert _max_run(sequence, "a") == 2  # naive weighting would run 5

    def test_the_pattern_repeats_each_cycle(self):
        wrr = SmoothWeightedRoundRobin(weights={"a": 3, "b": 2})
        first = wrr.cycle()
        assert wrr.cycle() == first


class TestRefusals:
    def test_no_servers_is_refused(self):
        with pytest.raises(Invalid):
            SmoothWeightedRoundRobin(weights={})

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            SmoothWeightedRoundRobin(weights={"a": 0})

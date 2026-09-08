from __future__ import annotations

from collections import Counter

import pytest

from rill.errors import Invalid
from rill.weightedrendezvous import owner

KEYS = [f"key-{number}" for number in range(9000)]


class TestProportional:
    def test_keys_split_in_proportion_to_weight(self):
        weights = {"a": 1.0, "b": 2.0, "c": 3.0}
        counts = Counter(owner(key, weights) for key in KEYS)
        fractions = {node: counts[node] / len(KEYS) for node in weights}
        assert abs(fractions["a"] - 1 / 6) < 0.03
        assert abs(fractions["b"] - 2 / 6) < 0.03
        assert abs(fractions["c"] - 3 / 6) < 0.03

    def test_double_weight_wins_about_double_the_keys(self):
        weights = {"x": 1.0, "y": 2.0}
        counts = Counter(owner(key, weights) for key in KEYS)
        assert 1.8 < counts["y"] / counts["x"] < 2.2


class TestRouting:
    def test_routing_is_deterministic(self):
        weights = {"a": 1.0, "b": 1.0}
        assert owner("key-1", weights) == owner("key-1", weights)


class TestRefusals:
    def test_no_nodes_is_refused(self):
        with pytest.raises(Invalid):
            owner("key", {})

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            owner("key", {"a": 0.0})

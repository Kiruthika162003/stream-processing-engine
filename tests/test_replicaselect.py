from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.replicaselect import ReplicaSelector


def _warmed() -> ReplicaSelector:
    selector = ReplicaSelector(alpha=0.3)
    for _ in range(10):
        selector.observe("a", 10)
        selector.observe("b", 10)
        selector.observe("c", 100)
    return selector


class TestRouting:
    def test_it_routes_around_the_slow_replica(self):
        selector = _warmed()
        assert round(selector.estimate("c"), 1) == 100.0
        assert selector.pick() in {"a", "b"}

    def test_a_recovered_replica_is_tried_again(self):
        selector = _warmed()
        for _ in range(10):
            selector.observe("c", 5)
        assert selector.pick() == "c"
        assert selector.estimate("c") < 10


class TestRefusals:
    def test_picking_before_any_observation_is_refused(self):
        with pytest.raises(Invalid):
            ReplicaSelector().pick()

    def test_a_negative_latency_is_refused(self):
        with pytest.raises(Invalid):
            ReplicaSelector().observe("a", -1)

    def test_an_alpha_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            ReplicaSelector(alpha=0)

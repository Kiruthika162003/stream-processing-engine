from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.metricstream import LatencyRing


def steady_ring() -> LatencyRing:
    ring = LatencyRing(capacity=100)
    for latency in range(1, 101):
        ring.observe(latency)
    return ring


class TestPercentiles:
    def test_nearest_rank_returns_observed_values(self):
        ring = steady_ring()
        assert ring.percentile(50) == 50
        assert ring.percentile(99) == 99
        assert ring.percentile(100) == 100

    def test_every_percentile_is_greppable(self):
        ring = steady_ring()
        for rank in (1, 25, 75, 90):
            assert ring.percentile(rank) in ring.ring

    def test_wild_ranks_and_empty_rings_are_refused(self):
        with pytest.raises(Invalid):
            steady_ring().percentile(0)
        with pytest.raises(Invalid):
            LatencyRing(capacity=50).percentile(50)

    def test_tiny_rings_cannot_pretend(self):
        with pytest.raises(Invalid):
            LatencyRing(capacity=5)


class TestTheWindow:
    def test_the_ring_evicts_the_oldest(self):
        ring = steady_ring()
        ring.observe(1000)
        assert len(ring.ring) == 100
        assert ring.total_seen == 101

    def test_the_evicted_worst_is_tracked_separately(self):
        ring = steady_ring()
        ring.observe(5000)
        for latency in [20] * 100:
            ring.observe(latency)
        report = ring.report()
        assert "worst ever served 5000" in report
        assert "the pager fires on that number" in report

    def test_a_calm_window_needs_no_tail_warning(self):
        report = steady_ring().report()
        assert "worst ever" not in report
        assert "grep for" in report

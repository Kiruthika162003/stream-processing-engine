from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.hedged import Hedger


class TestSingleRequest:
    def test_a_fast_primary_never_hedges(self):
        hedger = Hedger(hedge_delay=50, backup_latency=20)
        assert not hedger.hedged(10)
        assert hedger.served(10) == 10

    def test_a_slow_primary_is_capped_by_the_backup(self):
        hedger = Hedger(hedge_delay=50, backup_latency=20)
        assert hedger.hedged(500)
        assert hedger.served(500) == 70

    def test_the_backup_only_helps_if_it_beats_the_primary(self):
        hedger = Hedger(hedge_delay=50, backup_latency=20)
        # primary finishes at 60, before the hedge at 50 + 20 = 70
        assert hedger.served(60) == 60


class TestTheTrade:
    def test_a_high_delay_buys_the_tail_back_cheaply(self):
        primaries = [10] * 95 + [500] * 5
        summary = Hedger(hedge_delay=50, backup_latency=20).batch(primaries)
        assert summary["p99"] == 70
        assert summary["hedge_rate"] == 0.05

    def test_a_low_delay_doubles_the_load_for_a_smaller_gain(self):
        primaries = [10] * 95 + [500] * 5
        summary = Hedger(hedge_delay=5, backup_latency=20).batch(primaries)
        assert summary["p99"] == 25
        assert summary["hedge_rate"] == 1.0

    def test_without_hedging_the_tail_is_the_slow_primary(self):
        primaries = [10] * 95 + [500] * 5
        summary = Hedger(hedge_delay=10**9, backup_latency=20).batch(primaries)
        assert summary["p99"] == 500
        assert summary["hedge_rate"] == 0.0


class TestRefusals:
    def test_a_negative_delay_is_refused(self):
        with pytest.raises(Invalid):
            Hedger(hedge_delay=-1, backup_latency=20)

    def test_an_empty_batch_is_refused(self):
        with pytest.raises(Invalid):
            Hedger(hedge_delay=50, backup_latency=20).batch([])

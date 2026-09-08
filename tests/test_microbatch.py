from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.microbatch import MicroBatcher


def batcher() -> MicroBatcher:
    return MicroBatcher(crate_size=5, flush_interval=10)


class TestTheTwoTriggers:
    def test_the_full_crate_ships_immediately(self):
        chosen = batcher()
        for number in range(4):
            assert chosen.offer(f"e{number}", now=1) is None
        verdict = chosen.offer("e4", now=2)
        assert verdict == "crate of 5 shipped (full crate)"

    def test_the_timer_ships_the_partial_crate(self):
        chosen = batcher()
        chosen.offer("e0", now=1)
        verdict = chosen.offer("e1", now=11)
        assert verdict == "crate of 2 shipped (timer)"

    def test_degenerate_knobs_are_refused(self):
        with pytest.raises(Invalid):
            MicroBatcher(crate_size=0, flush_interval=5)


class TestShutdown:
    def test_the_stranded_crate_is_the_missing_order(self):
        chosen = batcher()
        chosen.offer("e0", now=1)
        verdict = chosen.shutdown(now=3)
        assert verdict.startswith("crate of 1 shipped (shutdown)")
        assert "someone's missing order" in verdict

    def test_a_clean_shutdown_says_so(self):
        assert batcher().shutdown(now=5) == (
            "nothing stranded; shutdown clean"
        )


class TestTheContract:
    def test_the_contract_prices_both_directions(self):
        chosen = batcher()
        for number in range(10):
            chosen.offer(f"e{number}", now=number)
        contract = chosen.contract()
        assert "2 request(s) instead of 10 (8 saved)" in contract
        assert "said aloud" in contract

    def test_no_traffic_no_contract(self):
        with pytest.raises(Invalid):
            batcher().contract()

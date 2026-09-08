from __future__ import annotations

import pytest

from rill.drr import DeficitRoundRobin
from rill.errors import Invalid


class TestOneRound:
    def test_a_quantum_serves_a_fair_slice_of_bytes_per_flow(self):
        drr = DeficitRoundRobin(quantum=100)
        for _ in range(5):
            drr.enqueue("big", 100)
        for _ in range(20):
            drr.enqueue("small", 10)
        served = drr.round()
        assert served["big"] == 100  # one large item
        assert served["small"] == 100  # ten small items

    def test_an_item_larger_than_the_quantum_waits_for_credit(self):
        drr = DeficitRoundRobin(quantum=100)
        drr.enqueue("f", 150)
        assert drr.round() == {}  # 100 credit, 150 item
        assert drr.round() == {"f": 150}  # 200 credit now covers it


class TestByteFairness:
    def test_flows_get_equal_bytes_despite_unequal_item_sizes(self):
        drr = DeficitRoundRobin(quantum=100)
        for _ in range(20):
            drr.enqueue("big", 100)
        for _ in range(200):
            drr.enqueue("small", 10)
        totals = {"big": 0, "small": 0}
        for _ in range(10):
            for flow, served_bytes in drr.round().items():
                totals[flow] += served_bytes
        assert totals["big"] == totals["small"] == 1000


class TestRefusals:
    def test_a_nonpositive_quantum_is_refused(self):
        with pytest.raises(Invalid):
            DeficitRoundRobin(quantum=0)

    def test_a_nonpositive_item_size_is_refused(self):
        with pytest.raises(Invalid):
            DeficitRoundRobin(quantum=100).enqueue("f", 0)

from __future__ import annotations

import pytest

from rill.crdtcounter import GCounter, PNCounter
from rill.errors import Invalid


class TestGCounter:
    def test_concurrent_increments_both_survive_the_merge(self):
        alice = GCounter("a")
        alice.increment(3)
        bob = GCounter("b")
        bob.increment(5)
        alice.merge(bob)
        assert alice.value() == 8

    def test_the_merge_is_idempotent(self):
        alice = GCounter("a")
        alice.increment(3)
        bob = GCounter("b")
        bob.increment(5)
        alice.merge(bob)
        alice.merge(bob)
        assert alice.value() == 8

    def test_the_merge_order_does_not_matter(self):
        a1 = GCounter("a")
        a1.increment(3)
        b1 = GCounter("b")
        b1.increment(5)
        left = GCounter("x")
        left.merge(a1)
        left.merge(b1)
        right = GCounter("y")
        right.merge(b1)
        right.merge(a1)
        assert left.value() == right.value() == 8

    def test_a_grow_only_counter_refuses_a_decrement(self):
        with pytest.raises(Invalid):
            GCounter("a").increment(-1)


class TestPNCounter:
    def test_a_pn_counter_can_go_down(self):
        counter = PNCounter("a")
        counter.increment(10)
        counter.decrement(4)
        assert counter.value() == 6

    def test_concurrent_up_and_down_merge_without_loss(self):
        alice = PNCounter("a")
        alice.increment(10)
        bob = PNCounter("b")
        bob.decrement(3)
        alice.merge(bob)
        assert alice.value() == 7

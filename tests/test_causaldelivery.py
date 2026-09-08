from __future__ import annotations

import pytest

from rill.causaldelivery import CausalDelivery
from rill.errors import Invalid


class TestCausalOrder:
    def test_a_reply_arriving_before_its_cause_is_buffered(self):
        node = CausalDelivery(nodes=("a", "b", "c"))
        delivered = node.receive("b", {"a": 1, "b": 1}, "reply")
        assert delivered == []
        assert node.pending() == 1

    def test_the_cause_arriving_flushes_the_buffered_reply_in_order(self):
        node = CausalDelivery(nodes=("a", "b", "c"))
        node.receive("b", {"a": 1, "b": 1}, "reply")  # held
        delivered = node.receive("a", {"a": 1}, "post")
        assert delivered == ["post", "reply"]
        assert node.pending() == 0

    def test_in_causal_order_messages_deliver_immediately(self):
        node = CausalDelivery(nodes=("a", "b"))
        assert node.receive("a", {"a": 1}, "first") == ["first"]
        assert node.receive("a", {"a": 2}, "second") == ["second"]


class TestRefusals:
    def test_an_unknown_sender_is_refused(self):
        node = CausalDelivery(nodes=("a",))
        with pytest.raises(Invalid):
            node.receive("z", {"z": 1}, "x")

    def test_no_nodes_is_refused(self):
        with pytest.raises(Invalid):
            CausalDelivery(nodes=())

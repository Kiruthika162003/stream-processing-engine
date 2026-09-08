from __future__ import annotations

import pytest

from rill.errors import Invalid, Missing
from rill.visibilitytimeout import VisibilityQueue


class TestDelivery:
    def test_a_received_message_is_hidden_until_acked(self):
        queue = VisibilityQueue(timeout=10)
        queue.send("m1")
        assert queue.receive(now=0) == "m1"
        assert queue.available() == 0
        assert queue.in_flight() == 1

    def test_an_ack_deletes_the_message_for_good(self):
        queue = VisibilityQueue(timeout=10)
        queue.send("m1")
        queue.receive(now=0)
        queue.ack("m1")
        queue.tick(now=100)
        assert queue.available() == 0
        assert queue.in_flight() == 0


class TestRedelivery:
    def test_an_unacked_message_reappears_after_the_timeout(self):
        queue = VisibilityQueue(timeout=10)
        queue.send("m1")
        queue.receive(now=0)
        queue.tick(now=10)  # timeout lapses unacked
        assert queue.available() == 1
        assert queue.receive(now=10) == "m1"  # redelivered

    def test_a_slow_consumer_gets_a_duplicate(self):
        queue = VisibilityQueue(timeout=10)
        queue.send("m1")
        first = queue.receive(now=0)
        # consumer still working at now=10, message redelivered to another
        second = queue.receive(now=10)
        assert first == second == "m1"  # processed twice


class TestRefusals:
    def test_receiving_from_an_empty_queue_is_missing(self):
        with pytest.raises(Missing):
            VisibilityQueue(timeout=10).receive(now=0)

    def test_acking_a_message_not_in_flight_is_refused(self):
        with pytest.raises(Invalid):
            VisibilityQueue(timeout=10).ack("ghost")

    def test_a_nonpositive_timeout_is_refused(self):
        with pytest.raises(Invalid):
            VisibilityQueue(timeout=0)

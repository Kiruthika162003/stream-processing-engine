from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.vectorclock import (
    AFTER,
    BEFORE,
    CONCURRENT,
    EQUAL,
    VectorClock,
    compare,
)


class TestCausalOrder:
    def test_a_message_makes_the_receiver_causally_after_the_sender(self):
        alice = VectorClock("a")
        sent = alice.tick()
        bob = VectorClock("b")
        after_receive = bob.receive(sent)
        assert compare(sent, after_receive) == BEFORE
        assert compare(after_receive, sent) == AFTER

    def test_receive_merges_by_elementwise_maximum(self):
        bob = VectorClock("b")
        bob.tick()
        merged = bob.receive({"a": 3, "b": 1})
        assert merged == {"a": 3, "b": 2}


class TestConcurrency:
    def test_independent_events_are_concurrent(self):
        alice = VectorClock("a")
        bob = VectorClock("b")
        assert compare(alice.tick(), bob.tick()) == CONCURRENT

    def test_the_scalar_would_have_ordered_these_concurrent_events(self):
        # both have a single tick; a scalar clock would call them
        # equal-or-ordered, the vector clock calls them concurrent.
        left = VectorClock("a").tick()
        right = VectorClock("b").tick()
        assert left != right
        assert compare(left, right) == CONCURRENT

    def test_identical_vectors_are_equal(self):
        assert compare({"a": 1}, {"a": 1}) == EQUAL


class TestRefusals:
    def test_two_empty_vectors_cannot_be_compared(self):
        with pytest.raises(Invalid):
            compare({}, {})

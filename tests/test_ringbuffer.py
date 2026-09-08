from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid, Missing
from rill.ringbuffer import RingBuffer


class TestOverwrite:
    def test_a_full_buffer_drops_the_oldest_and_returns_it(self):
        ring = RingBuffer(capacity=3, overwrite=True)
        for item in ("a", "b", "c"):
            assert ring.push(item) is None
        assert ring.push("d") == "a"
        assert ring.snapshot() == ["b", "c", "d"]

    def test_the_window_holds_the_most_recent_items(self):
        ring = RingBuffer(capacity=2, overwrite=True)
        for item in ("a", "b", "c", "d"):
            ring.push(item)
        assert ring.snapshot() == ["c", "d"]


class TestReject:
    def test_a_full_reject_buffer_refuses_the_newest(self):
        ring = RingBuffer(capacity=2, overwrite=False)
        ring.push("a")
        ring.push("b")
        with pytest.raises(Halted):
            ring.push("c")
        assert ring.snapshot() == ["a", "b"]


class TestPop:
    def test_pop_returns_in_fifo_order(self):
        ring = RingBuffer(capacity=3)
        ring.push("a")
        ring.push("b")
        assert ring.pop() == "a"
        assert ring.pop() == "b"

    def test_popping_empty_is_missing(self):
        with pytest.raises(Missing):
            RingBuffer(capacity=2).pop()

    def test_pop_then_push_wraps_correctly(self):
        ring = RingBuffer(capacity=3)
        for item in ("a", "b", "c"):
            ring.push(item)
        ring.pop()
        ring.push("d")
        assert ring.snapshot() == ["b", "c", "d"]


class TestRefusals:
    def test_a_nonpositive_capacity_is_refused(self):
        with pytest.raises(Invalid):
            RingBuffer(capacity=0)

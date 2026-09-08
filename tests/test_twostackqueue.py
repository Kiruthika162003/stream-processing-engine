from __future__ import annotations

import random

import pytest

from rill.errors import Missing
from rill.twostackqueue import TwoStackQueue


class TestFifo:
    def test_it_dequeues_in_enqueue_order(self):
        queue = TwoStackQueue()
        for item in "abc":
            queue.enqueue(item)
        assert [queue.dequeue() for _ in range(3)] == ["a", "b", "c"]

    def test_interleaved_operations_keep_order(self):
        queue = TwoStackQueue()
        queue.enqueue("a")
        queue.enqueue("b")
        assert queue.dequeue() == "a"
        queue.enqueue("c")
        assert queue.dequeue() == "b"
        assert queue.dequeue() == "c"


class TestAmortized:
    def test_each_element_is_moved_at_most_once(self):
        queue = TwoStackQueue()
        rng = random.Random(1)
        enqueued = 0
        for _ in range(10000):
            if rng.random() < 0.5 or len(queue) == 0:
                queue.enqueue("x")
                enqueued += 1
            else:
                queue.dequeue()
        while len(queue):
            queue.dequeue()
        # linear total moves, not quadratic: each element crosses once
        assert queue.moves() == enqueued


class TestRefusals:
    def test_dequeuing_an_empty_queue_is_missing(self):
        with pytest.raises(Missing):
            TwoStackQueue().dequeue()

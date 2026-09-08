from __future__ import annotations

import random
from collections import deque

import pytest

from rill.errors import Missing
from rill.minqueue import MinQueue


class TestMinimum:
    def test_the_minimum_tracks_the_queue(self):
        queue = MinQueue()
        for value in (3, 1, 4, 1, 5):
            queue.enqueue(value)
        assert queue.minimum() == 1

    def test_the_minimum_survives_a_dequeue_of_a_duplicate_min(self):
        queue = MinQueue()
        for value in (3, 1, 4, 1, 5):
            queue.enqueue(value)
        queue.dequeue()  # 3
        queue.dequeue()  # the first 1
        assert queue.minimum() == 1  # the second 1 remains

    def test_it_matches_a_naive_model(self):
        rng = random.Random(5)
        for _ in range(500):
            queue = MinQueue()
            model: deque[int] = deque()
            for _ in range(rng.randint(1, 40)):
                if rng.random() < 0.6 or not model:
                    value = rng.randint(-20, 20)
                    queue.enqueue(value)
                    model.append(value)
                else:
                    assert queue.dequeue() == model.popleft()
                if model:
                    assert queue.minimum() == min(model)


class TestFifo:
    def test_dequeue_is_first_in_first_out(self):
        queue = MinQueue()
        queue.enqueue(1)
        queue.enqueue(2)
        assert queue.dequeue() == 1
        assert queue.dequeue() == 2


class TestRefusals:
    def test_dequeuing_empty_is_missing(self):
        with pytest.raises(Missing):
            MinQueue().dequeue()

    def test_the_minimum_of_empty_is_missing(self):
        with pytest.raises(Missing):
            MinQueue().minimum()

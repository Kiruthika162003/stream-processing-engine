from __future__ import annotations

import random

import pytest

from rill.errors import Missing
from rill.minstack import MinStack


class TestMinimum:
    def test_the_minimum_tracks_the_pushes(self):
        stack = MinStack()
        for value in (3, 1, 4, 1, 5):
            stack.push(value)
        assert stack.minimum() == 1

    def test_the_minimum_is_restored_as_values_pop(self):
        stack = MinStack()
        for value in (5, 2, 8, 1):
            stack.push(value)
        assert stack.minimum() == 1
        stack.pop()  # remove 1
        assert stack.minimum() == 2  # the min before 1 was pushed

    def test_it_matches_a_naive_model(self):
        rng = random.Random(4)
        for _ in range(500):
            stack = MinStack()
            model: list[int] = []
            for _ in range(rng.randint(1, 40)):
                if rng.random() < 0.6 or not model:
                    value = rng.randint(-20, 20)
                    stack.push(value)
                    model.append(value)
                else:
                    assert stack.pop() == model.pop()
                if model:
                    assert stack.minimum() == min(model)


class TestLifo:
    def test_pop_returns_last_in_first_out(self):
        stack = MinStack()
        stack.push(1)
        stack.push(2)
        assert stack.pop() == 2
        assert stack.pop() == 1


class TestRefusals:
    def test_popping_empty_is_missing(self):
        with pytest.raises(Missing):
            MinStack().pop()

    def test_the_minimum_of_empty_is_missing(self):
        with pytest.raises(Missing):
            MinStack().minimum()

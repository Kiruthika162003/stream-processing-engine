from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.stockspan import spans


def _brute(values: list[int]) -> list[int]:
    out = []
    for i in range(len(values)):
        span = 1
        j = i - 1
        while j >= 0 and values[j] <= values[i]:
            span += 1
            j -= 1
        out.append(span)
    return out


class TestCorrectness:
    def test_the_classic_series(self):
        assert spans([100, 80, 60, 70, 60, 75, 85]) == [1, 1, 1, 2, 1, 4, 6]

    def test_it_matches_brute_force(self):
        rng = random.Random(4)
        for _ in range(500):
            values = [rng.randint(0, 10) for _ in range(rng.randint(1, 20))]
            assert spans(values) == _brute(values)


class TestShapes:
    def test_a_rising_series_grows_the_span(self):
        assert spans([1, 2, 3, 4]) == [1, 2, 3, 4]

    def test_a_falling_series_keeps_span_one(self):
        assert spans([4, 3, 2, 1]) == [1, 1, 1, 1]


class TestRefusals:
    def test_an_empty_series_is_refused(self):
        with pytest.raises(Invalid):
            spans([])

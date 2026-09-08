from __future__ import annotations

import random

import pytest

from rill.errors import Invalid, Missing
from rill.slidingmax import SlidingMax


class TestCorrectness:
    def test_the_window_max_matches_brute_force(self):
        rng = random.Random(2)
        window, length = 50, 2000
        sliding = SlidingMax(window=window)
        seen: list[int] = []
        for step in range(length):
            value = rng.randint(0, 1000)
            seen.append(value)
            sliding.push(value)
            expected = max(seen[max(0, step - window + 1) : step + 1])
            assert sliding.maximum() == expected

    def test_the_max_falls_when_the_peak_leaves_the_window(self):
        sliding = SlidingMax(window=2)
        sliding.push(9)
        sliding.push(1)
        assert sliding.maximum() == 9
        sliding.push(2)  # 9 now out of the two-wide window
        assert sliding.maximum() == 2


class TestLinearWork:
    def test_total_work_is_linear_regardless_of_window(self):
        window, length = 50, 2000
        sliding = SlidingMax(window=window)
        rng = random.Random(2)
        for _ in range(length):
            sliding.push(rng.randint(0, 1000))
        # each element is pushed once and popped at most twice
        assert sliding.total_ops() <= 3 * length
        # dramatically less than the naive rescan of n * window
        assert sliding.total_ops() < length * window // 10


class TestRefusals:
    def test_a_nonpositive_window_is_refused(self):
        with pytest.raises(Invalid):
            SlidingMax(window=0)

    def test_the_max_of_an_empty_window_is_missing(self):
        with pytest.raises(Missing):
            SlidingMax(window=3).maximum()

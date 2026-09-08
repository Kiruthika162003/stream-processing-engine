from __future__ import annotations

import random
from collections import deque

import pytest

from rill.errors import Invalid
from rill.windoweddistinct import WindowedDistinct


class TestCounting:
    def test_it_counts_distinct_within_the_window(self):
        counter = WindowedDistinct(window=3)
        for value in ("a", "b", "a"):
            counter.add(value)
        assert counter.distinct() == 2  # a, b

    def test_an_evicted_duplicate_does_not_drop_the_count(self):
        counter = WindowedDistinct(window=2)
        counter.add("a")
        counter.add("a")  # window [a, a], distinct 1
        counter.add("b")  # window [a, b], the evicted a still leaves one a
        assert counter.distinct() == 2

    def test_it_matches_a_recompute_over_random_streams(self):
        rng = random.Random(3)
        for _ in range(200):
            window = rng.randint(1, 20)
            counter = WindowedDistinct(window=window)
            recent: deque[str] = deque()
            for _ in range(rng.randint(1, 60)):
                value = str(rng.randint(0, 10))
                counter.add(value)
                recent.append(value)
                if len(recent) > window:
                    recent.popleft()
                assert counter.distinct() == len(set(recent))


class TestRefusals:
    def test_a_nonpositive_window_is_refused(self):
        with pytest.raises(Invalid):
            WindowedDistinct(window=0)

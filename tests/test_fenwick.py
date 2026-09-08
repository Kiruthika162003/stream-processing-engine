from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.fenwick import Fenwick


class TestCorrectness:
    def test_prefix_matches_a_brute_force_sum(self):
        rng = random.Random(5)
        size = 1024
        tree = Fenwick(size=size)
        raw = [0] * size
        for _ in range(5000):
            index = rng.randrange(size)
            delta = rng.randint(1, 10)
            tree.add(index, delta)
            raw[index] += delta
        for probe in (0, 100, 500, 1023):
            assert tree.prefix(probe) == sum(raw[: probe + 1])

    def test_range_sum_matches_brute_force(self):
        tree = Fenwick(size=64)
        for index in range(64):
            tree.add(index, index)
        assert tree.range_sum(10, 20) == sum(range(10, 21))


class TestLogarithmicCost:
    def test_a_prefix_touches_log_cells_not_linear(self):
        size = 1024
        tree = Fenwick(size=size)
        for index in range(size):
            tree.add(index, 1)
        # index 1022 has cursor 1023, all ten bits set: ten cells
        tree.prefix(1022)
        assert tree.last_touches() == 10
        assert tree.last_touches() < size

    def test_an_update_touches_log_cells(self):
        tree = Fenwick(size=1024)
        tree.add(0, 1)
        assert tree.last_touches() == 11


class TestRefusals:
    def test_a_nonpositive_size_is_refused(self):
        with pytest.raises(Invalid):
            Fenwick(size=0)

    def test_an_out_of_range_index_is_refused(self):
        with pytest.raises(Invalid):
            Fenwick(size=8).add(8, 1)

    def test_an_inverted_range_is_refused(self):
        with pytest.raises(Invalid):
            Fenwick(size=8).range_sum(5, 2)

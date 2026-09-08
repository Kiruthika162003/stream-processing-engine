from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.skiplist import SkipList


class TestOrderedSet:
    def test_it_keeps_keys_sorted(self):
        rng = random.Random(9)
        sl = SkipList(coin=lambda: rng.random() < 0.5)
        for key in (5, 1, 9, 3, 7):
            sl.insert(key)
        assert sl.to_list() == [1, 3, 5, 7, 9]

    def test_membership_is_answered_both_ways(self):
        rng = random.Random(1)
        sl = SkipList(coin=lambda: rng.random() < 0.5)
        for key in range(10):
            sl.insert(key)
        assert sl.contains(7)
        assert not sl.contains(11)

    def test_a_duplicate_insert_is_ignored(self):
        sl = SkipList(coin=lambda: False)
        sl.insert(4)
        sl.insert(4)
        assert sl.to_list() == [4]


class TestCoinDrivesCost:
    def test_a_fair_coin_searches_in_log_visits(self):
        rng = random.Random(9)
        sl = SkipList(coin=lambda: rng.random() < 0.5)
        for key in range(1000):
            sl.insert(key)
        sl.contains(999)
        assert sl.last_visited() < 30

    def test_a_coin_that_never_promotes_degrades_to_linear(self):
        sl = SkipList(coin=lambda: False)
        for key in range(1000):
            sl.insert(key)
        sl.contains(999)
        assert sl.last_visited() >= 900


class TestRefusals:
    def test_a_nonpositive_max_level_is_refused(self):
        with pytest.raises(Invalid):
            SkipList(coin=lambda: False, max_level=0)

from __future__ import annotations

import pytest

from rill.coinchange import IMPOSSIBLE, greedy_coins, min_coins
from rill.errors import Invalid


class TestGreedyFailsOnNonCanonical:
    def test_dp_beats_greedy_on_a_non_canonical_system(self):
        coins = [1, 3, 4]
        assert min_coins(coins, 6) == 2  # 3 + 3
        assert greedy_coins(coins, 6) == 3  # 4 + 1 + 1

    def test_greedy_matches_dp_on_the_canonical_us_system(self):
        coins = [1, 5, 10, 25]
        assert min_coins(coins, 63) == 6
        assert greedy_coins(coins, 63) == 6


class TestEdges:
    def test_an_unmakeable_amount_is_impossible(self):
        assert min_coins([3, 5], 1) == IMPOSSIBLE
        assert greedy_coins([3, 5], 1) == IMPOSSIBLE

    def test_zero_needs_no_coins(self):
        assert min_coins([1, 2], 0) == 0


class TestRefusals:
    def test_a_negative_amount_is_refused(self):
        with pytest.raises(Invalid):
            min_coins([1], -1)

    def test_a_nonpositive_coin_is_refused(self):
        with pytest.raises(Invalid):
            min_coins([0], 5)

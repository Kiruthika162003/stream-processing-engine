from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.powerof2 import imbalance, max_load

BALLS, BINS = 10000, 1000


def _peak(choices: int) -> int:
    rng = random.Random(4)
    return max_load(BALLS, BINS, choices, rng.randrange)


class TestTheSecondChoice:
    def test_a_single_choice_leaves_a_tall_peak(self):
        assert _peak(1) == 24  # average is 10

    def test_the_second_choice_roughly_halves_the_peak(self):
        assert _peak(2) == 12

    def test_a_third_choice_gives_diminishing_returns(self):
        assert _peak(3) == 11
        assert _peak(2) - _peak(3) < _peak(1) - _peak(2)


class TestImbalance:
    def test_imbalance_is_the_peak_above_the_average(self):
        rng = random.Random(4)
        gap = imbalance(BALLS, BINS, 1, rng.randrange)
        assert gap == 14  # 24 peak minus 10 average


class TestRefusals:
    def test_zero_bins_is_refused(self):
        with pytest.raises(Invalid):
            max_load(10, 0, 1, lambda _bins: 0)

    def test_zero_choices_is_refused(self):
        with pytest.raises(Invalid):
            max_load(10, 5, 0, lambda _bins: 0)

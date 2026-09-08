from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.welford import Welford, naive_variance

BIG = 1e9
OFFSET = [BIG + 1, BIG + 2, BIG + 3, BIG + 4, BIG + 5]


class TestStability:
    def test_welford_is_exact_on_large_offset_data(self):
        welford = Welford()
        for sample in OFFSET:
            welford.update(sample)
        assert welford.variance() == 2.0  # true variance of 1..5

    def test_the_naive_formula_cancels_to_zero(self):
        assert naive_variance(OFFSET) == 0.0  # catastrophically wrong

    def test_both_agree_on_small_numbers(self):
        small = [1, 2, 3, 4, 5]
        welford = Welford()
        for sample in small:
            welford.update(sample)
        assert welford.variance() == naive_variance(small) == 2.0


class TestMean:
    def test_the_running_mean_is_correct(self):
        welford = Welford()
        for sample in (2, 4, 6):
            welford.update(sample)
        assert welford.mean() == 4.0


class TestRefusals:
    def test_variance_before_any_sample_is_refused(self):
        with pytest.raises(Invalid):
            Welford().variance()

    def test_naive_of_nothing_is_refused(self):
        with pytest.raises(Invalid):
            naive_variance([])

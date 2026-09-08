from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.kahan import KahanSum, naive_sum

MILLION = 1_000_000
TRUE = 100000.0


class TestDrift:
    def test_kahan_sums_a_million_tenths_exactly(self):
        kahan = KahanSum()
        for _ in range(MILLION):
            kahan.add(0.1)
        assert kahan.total() == TRUE

    def test_the_naive_sum_drifts_off_the_truth(self):
        drifted = naive_sum([0.1] * MILLION)
        assert drifted != TRUE
        assert abs(drifted - TRUE) > 0

    def test_kahan_is_closer_to_the_truth_than_naive(self):
        kahan = KahanSum()
        for _ in range(MILLION):
            kahan.add(0.1)
        naive = naive_sum([0.1] * MILLION)
        assert abs(kahan.total() - TRUE) < abs(naive - TRUE)


class TestBasics:
    def test_small_sums_are_exact_both_ways(self):
        kahan = KahanSum()
        for value in (1.0, 2.0, 3.0):
            kahan.add(value)
        assert kahan.total() == 6.0
        assert naive_sum([1.0, 2.0, 3.0]) == 6.0


class TestRefusals:
    def test_naive_of_nothing_is_refused(self):
        with pytest.raises(Invalid):
            naive_sum([])

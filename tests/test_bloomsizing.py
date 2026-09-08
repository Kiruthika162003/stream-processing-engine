from __future__ import annotations

import pytest

from rill.bloomsizing import bits_for, false_positive_rate, optimal_hashes
from rill.errors import Invalid


class TestSizing:
    def test_one_percent_costs_about_ten_bits_per_element(self):
        bits = bits_for(1000, 0.01)
        assert round(bits / 1000, 1) == 9.6

    def test_a_tenth_of_a_percent_costs_about_fourteen(self):
        bits = bits_for(1000, 0.001)
        assert round(bits / 1000, 1) == 14.4

    def test_the_optimal_hash_count_hits_the_target_rate(self):
        bits = bits_for(1000, 0.01)
        hashes = optimal_hashes(bits, 1000)
        assert hashes == 7
        assert false_positive_rate(bits, 1000, hashes) == pytest.approx(0.01, abs=0.001)


class TestOptimumIsInBetween:
    def test_too_few_or_too_many_hashes_are_both_worse(self):
        bits = bits_for(1000, 0.01)
        best = false_positive_rate(bits, 1000, optimal_hashes(bits, 1000))
        assert false_positive_rate(bits, 1000, 1) > best
        assert false_positive_rate(bits, 1000, 20) > best


class TestRefusals:
    def test_a_target_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            bits_for(1000, 1.0)

    def test_nonpositive_elements_are_refused(self):
        with pytest.raises(Invalid):
            bits_for(0, 0.01)

from __future__ import annotations

import math

import pytest

from rill.errors import Invalid
from rill.sieve import factorize, linear_sieve


class TestPrimeCounts:
    @pytest.mark.parametrize(
        ("limit", "expected"),
        [(100, 25), (1000, 168), (10000, 1229), (100000, 9592)],
    )
    def test_pi_matches_the_known_prime_counting_function(self, limit, expected):
        primes, _ = linear_sieve(limit)
        assert len(primes) == expected

    def test_the_first_primes_are_right(self):
        primes, _ = linear_sieve(30)
        assert primes == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

    def test_a_prime_is_its_own_smallest_factor(self):
        _, spf = linear_sieve(20)
        assert spf[13] == 13
        assert spf[12] == 2


class TestFactorize:
    def test_a_concrete_factorization(self):
        _, spf = linear_sieve(1000)
        assert factorize(360, spf) == [2, 2, 2, 3, 3, 5]

    def test_the_factors_reconstruct_and_are_sorted(self):
        _, spf = linear_sieve(10000)
        for n in range(2, 10001):
            factors = factorize(n, spf)
            assert math.prod(factors) == n
            assert factors == sorted(factors)

    def test_one_has_no_factors(self):
        _, spf = linear_sieve(10)
        assert factorize(1, spf) == []


class TestRefusals:
    def test_a_negative_limit_is_refused(self):
        with pytest.raises(Invalid):
            linear_sieve(-1)

    def test_zero_is_refused_for_factorize(self):
        _, spf = linear_sieve(10)
        with pytest.raises(Invalid):
            factorize(0, spf)

    def test_a_number_beyond_the_range_is_refused(self):
        _, spf = linear_sieve(10)
        with pytest.raises(Invalid):
            factorize(999, spf)

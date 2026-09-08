from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.karatsuba import karatsuba


class TestProduct:
    def test_small_products_are_exact(self):
        assert karatsuba(0, 999) == 0
        assert karatsuba(6, 7) == 42
        assert karatsuba(12345, 6789) == 12345 * 6789

    def test_it_matches_native_multiply_over_random_numbers(self):
        rng = random.Random(23)
        for _ in range(5000):
            x = rng.randint(0, 10 ** rng.randint(1, 40))
            y = rng.randint(0, 10 ** rng.randint(1, 40))
            if rng.random() < 0.3:
                x = -x
            if rng.random() < 0.3:
                y = -y
            assert karatsuba(x, y) == x * y

    def test_a_two_hundred_digit_product_is_exact(self):
        a = random.Random(1).randint(10**200, 10**201)
        b = random.Random(2).randint(10**200, 10**201)
        assert karatsuba(a, b) == a * b


class TestSigns:
    def test_negative_times_positive_is_negative(self):
        assert karatsuba(-12345678901234567890, 98765) == (
            -12345678901234567890 * 98765
        )

    def test_negative_times_negative_is_positive(self):
        assert karatsuba(-10**30, -10**30) == 10**60


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            karatsuba(None, 5)

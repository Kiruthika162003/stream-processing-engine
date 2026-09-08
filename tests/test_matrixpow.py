from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.matrixpow import fibonacci, matrix_power, multiply


def _iterative_fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class TestMultiply:
    def test_a_concrete_product(self):
        assert multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]]) == [[19, 22], [43, 50]]

    def test_mismatched_dimensions_are_refused(self):
        with pytest.raises(Invalid):
            multiply([[1, 2, 3]], [[1, 2]])


class TestPower:
    def test_the_zeroth_power_is_the_identity(self):
        assert matrix_power([[2, 3], [1, 4]], 0) == [[1, 0], [0, 1]]

    def test_a_diagonal_matrix_powers_entrywise(self):
        assert matrix_power([[2, 0], [0, 3]], 10) == [[1024, 0], [0, 59049]]

    def test_a_non_square_matrix_is_refused(self):
        with pytest.raises(Invalid):
            matrix_power([[1, 2, 3], [4, 5, 6]], 2)

    def test_a_negative_exponent_is_refused(self):
        with pytest.raises(Invalid):
            matrix_power([[1, 1], [1, 0]], -1)


class TestFibonacci:
    def test_it_matches_the_iterative_fibonacci(self):
        for n in range(200):
            assert fibonacci(n) == _iterative_fib(n)

    def test_a_large_term_is_exact(self):
        assert fibonacci(100) == 354224848179261915075

    def test_a_negative_index_is_refused(self):
        with pytest.raises(Invalid):
            fibonacci(-1)

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.linearrecurrence import nth_term


def _fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _trib(n: int) -> int:
    seq = [0, 0, 1]
    for _i in range(3, n + 1):
        seq.append(seq[-1] + seq[-2] + seq[-3])
    return seq[n]


class TestFibonacci:
    def test_it_matches_the_iteration(self):
        assert all(nth_term([1, 1], [0, 1], n) == _fib(n) for n in range(30))

    def test_a_far_term_is_exact(self):
        assert nth_term([1, 1], [0, 1], 50) == 12586269025

    def test_the_base_terms_are_the_initial_values(self):
        assert nth_term([1, 1], [0, 1], 0) == 0
        assert nth_term([1, 1], [0, 1], 1) == 1


class TestHigherOrder:
    def test_tribonacci_matches_the_iteration(self):
        assert all(nth_term([1, 1, 1], [0, 0, 1], n) == _trib(n) for n in range(20))


class TestRefusals:
    def test_mismatched_lengths_are_refused(self):
        with pytest.raises(Invalid):
            nth_term([1, 1], [0], 5)

    def test_a_negative_n_is_refused(self):
        with pytest.raises(Invalid):
            nth_term([1, 1], [0, 1], -1)

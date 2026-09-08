from __future__ import annotations

import math

import pytest

from rill.errors import Invalid
from rill.rootfind import bisect_root, newton_root


def _f(x: float) -> float:
    return x * x - 2


def _df(x: float) -> float:
    return 2 * x


class TestConvergence:
    def test_both_find_the_root(self):
        bisect, _ = bisect_root(_f, 0, 2)
        newton, _ = newton_root(_f, _df, 2.0)
        assert abs(bisect - math.sqrt(2)) < 1e-8
        assert abs(newton - math.sqrt(2)) < 1e-8

    def test_newton_converges_in_far_fewer_iterations(self):
        _, bisect_iters = bisect_root(_f, 0, 2)
        _, newton_iters = newton_root(_f, _df, 2.0)
        assert newton_iters < 10
        assert bisect_iters > 30
        assert newton_iters < bisect_iters


class TestFailureModes:
    def test_newton_can_fail_to_converge_from_a_bad_start(self):
        # x^3 - 2x + 2 at x=0 cycles under Newton
        with pytest.raises(Invalid):
            newton_root(lambda x: x**3 - 2 * x + 2, lambda x: 3 * x * x - 2, 0.0)

    def test_bisection_needs_a_bracketed_sign_change(self):
        with pytest.raises(Invalid):
            bisect_root(_f, 2, 3)  # both endpoints positive


class TestRefusals:
    def test_a_nonpositive_tolerance_is_refused(self):
        with pytest.raises(Invalid):
            bisect_root(_f, 0, 2, tolerance=0)

    def test_a_zero_derivative_is_refused(self):
        with pytest.raises(Invalid):
            newton_root(_f, lambda _x: 0.0, 1.0)

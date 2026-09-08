from __future__ import annotations

import math

import pytest

from rill.errors import Invalid
from rill.simpson import integrate


class TestExactness:
    def test_it_is_exact_on_a_cubic(self):
        def f(x):
            return 2 * x**3 - 3 * x**2 + x + 5

        def antideriv(t):
            return 0.5 * t**4 - t**3 + 0.5 * t**2 + 5 * t

        exact = antideriv(4) - antideriv(0)
        # even with the minimum two intervals, Simpson is exact for cubics
        assert integrate(f, 0, 4, 2) == pytest.approx(exact)

    def test_it_is_exact_on_a_line_and_a_constant(self):
        assert integrate(lambda _x: 3.0, 0, 10, 2) == pytest.approx(30.0)
        assert integrate(lambda x: 2 * x, 0, 5, 4) == pytest.approx(25.0)

    def test_a_zero_width_interval_is_zero(self):
        assert integrate(math.sin, 2, 2, 2) == 0.0


class TestConvergence:
    def test_it_converges_on_the_sine(self):
        v = integrate(math.sin, 0, math.pi, 64)
        assert abs(v - 2.0) < 1e-6

    def test_the_error_drops_about_sixteenfold_per_halved_step(self):
        e1 = abs(integrate(math.sin, 0, math.pi, 16) - 2.0)
        e2 = abs(integrate(math.sin, 0, math.pi, 32) - 2.0)
        assert 12 < e1 / e2 < 20  # fourth-order: ~16


class TestRefusals:
    def test_odd_intervals_are_refused(self):
        with pytest.raises(Invalid):
            integrate(math.sin, 0, 1, 3)

    def test_zero_intervals_are_refused(self):
        with pytest.raises(Invalid):
            integrate(math.sin, 0, 1, 0)

    def test_a_missing_function_is_refused(self):
        with pytest.raises(Invalid):
            integrate(None, 0, 1, 2)

    def test_a_reversed_interval_is_refused(self):
        with pytest.raises(Invalid):
            integrate(math.sin, 5, 1, 2)

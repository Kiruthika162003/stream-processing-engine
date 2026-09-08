from __future__ import annotations

import math
import random

import pytest

from rill.errors import Invalid
from rill.ternarysearch import ternary_search_max


class TestPeaks:
    def test_a_quadratic_peak(self):
        got = ternary_search_max(lambda x: -(x - 3) ** 2 + 5, -10, 10)
        assert abs(got - 3) < 1e-6

    def test_a_quartic_peak(self):
        got = ternary_search_max(lambda x: -((x - 2) ** 4), -5, 5)
        assert abs(got - 2) < 1e-3

    def test_the_sine_peak_on_its_first_arch(self):
        got = ternary_search_max(math.sin, 0, math.pi)
        assert abs(got - math.pi / 2) < 1e-6

    def test_it_matches_a_fine_brute_grid(self):
        rng = random.Random(31)
        for _ in range(300):
            peak = rng.uniform(-8, 8)
            a = rng.uniform(0.1, 3)

            def f(x, peak=peak, a=a):
                return -a * (x - peak) ** 2 + 5

            assert abs(ternary_search_max(f, -10, 10) - peak) < 1e-6


class TestRefusals:
    def test_a_missing_function_is_refused(self):
        with pytest.raises(Invalid):
            ternary_search_max(None, 0, 1)

    def test_a_reversed_interval_is_refused(self):
        with pytest.raises(Invalid):
            ternary_search_max(lambda x: -x * x, 5, 1)

    def test_a_non_positive_tolerance_is_refused(self):
        with pytest.raises(Invalid):
            ternary_search_max(lambda x: -x * x, 0, 1, tolerance=0)

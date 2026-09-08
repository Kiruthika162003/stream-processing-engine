from __future__ import annotations

import pytest

from rill.aimd import AimdLimiter
from rill.errors import Invalid


class TestSlopes:
    def test_success_increases_the_limit_by_one(self):
        limiter = AimdLimiter(limit=10, floor=1, ceiling=100)
        assert limiter.on_success() == 11
        assert limiter.on_success() == 12

    def test_overload_halves_the_limit(self):
        limiter = AimdLimiter(limit=64, floor=1, ceiling=100)
        assert limiter.on_overload() == 32
        assert limiter.on_overload() == 16

    def test_the_limit_never_leaves_its_bounds(self):
        limiter = AimdLimiter(limit=2, floor=2, ceiling=3)
        assert limiter.on_overload() == 2
        limiter.on_success()
        assert limiter.on_success() == 3


class TestAsymmetry:
    def test_the_retreat_is_logarithmic_and_the_climb_is_linear(self):
        limiter = AimdLimiter(limit=64, floor=1, ceiling=64)
        # falling 64 to 1 takes six halvings; climbing back takes 63 steps.
        assert limiter.overloads_to_floor() == 6
        limiter.limit = 1
        assert limiter.successes_to_ceiling() == 63


class TestRefusals:
    def test_a_limit_outside_the_bounds_is_refused(self):
        with pytest.raises(Invalid):
            AimdLimiter(limit=200, floor=1, ceiling=100)

    def test_a_floor_below_one_is_refused(self):
        with pytest.raises(Invalid):
            AimdLimiter(limit=0, floor=0, ceiling=10)

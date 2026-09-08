from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.slidingwindowrate import FixedWindowLimiter, SlidingLogLimiter


class TestFixedWindowSeam:
    def test_the_fixed_window_leaks_double_across_the_seam(self):
        limiter = FixedWindowLimiter(limit=5, window=60)
        admitted = sum(limiter.allow(59) for _ in range(5))
        admitted += sum(limiter.allow(60) for _ in range(5))
        assert admitted == 10

    def test_within_one_window_the_fixed_limiter_holds(self):
        limiter = FixedWindowLimiter(limit=5, window=60)
        admitted = sum(limiter.allow(10) for _ in range(8))
        assert admitted == 5


class TestSlidingLog:
    def test_the_sliding_log_holds_the_limit_across_the_seam(self):
        limiter = SlidingLogLimiter(limit=5, window=60)
        admitted = sum(limiter.allow(59) for _ in range(5))
        admitted += sum(limiter.allow(60) for _ in range(5))
        assert admitted == 5

    def test_the_sliding_log_admits_again_once_stamps_age_out(self):
        limiter = SlidingLogLimiter(limit=2, window=10)
        assert limiter.allow(0)
        assert limiter.allow(1)
        assert not limiter.allow(2)
        assert limiter.allow(11)


class TestRefusals:
    def test_a_nonpositive_fixed_setting_is_refused(self):
        with pytest.raises(Invalid):
            FixedWindowLimiter(limit=0, window=60)

    def test_a_nonpositive_sliding_setting_is_refused(self):
        with pytest.raises(Invalid):
            SlidingLogLimiter(limit=5, window=0)

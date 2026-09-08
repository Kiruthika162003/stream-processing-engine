from __future__ import annotations

import pytest

from rill.backoff import Backoff, cohort_spread
from rill.errors import Invalid


class TestExponential:
    def test_the_delay_doubles_until_the_cap(self):
        backoff = Backoff(base=1, factor=2, cap=100)
        assert [backoff.delay(n) for n in range(5)] == [1, 2, 4, 8, 16]

    def test_the_cap_holds_the_delay_down(self):
        backoff = Backoff(base=1, factor=2, cap=10)
        assert backoff.delay(10) == 10


class TestLockstepWithoutJitter:
    def test_a_cohort_on_the_same_attempt_lands_at_one_instant(self):
        backoff = Backoff(base=1, factor=2, cap=1000)
        herd = [backoff.delay(6) for _ in range(50)]
        assert cohort_spread(herd) == 0

    def test_full_jitter_smears_the_cohort_across_the_window(self):
        backoff = Backoff(base=1, factor=2, cap=1000)
        rolls = [n / 50 for n in range(50)]
        herd = [backoff.full_jitter(6, roll) for roll in rolls]
        assert cohort_spread(herd) > 0
        assert max(herd) <= backoff.delay(6)


class TestEqualJitter:
    def test_equal_jitter_keeps_a_floor_under_the_wait(self):
        backoff = Backoff(base=1, factor=2, cap=1000)
        floor = backoff.delay(6) // 2
        assert backoff.equal_jitter(6, 0.0) == floor
        assert backoff.equal_jitter(6, 0.999) >= floor


class TestRefusals:
    def test_a_nonpositive_base_is_refused(self):
        with pytest.raises(Invalid):
            Backoff(base=0, factor=2, cap=10)

    def test_a_roll_outside_the_unit_interval_is_refused(self):
        backoff = Backoff(base=1, factor=2, cap=10)
        with pytest.raises(Invalid):
            backoff.full_jitter(1, 1.0)

    def test_a_negative_attempt_is_refused(self):
        backoff = Backoff(base=1, factor=2, cap=10)
        with pytest.raises(Invalid):
            backoff.delay(-1)

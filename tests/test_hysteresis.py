from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.hysteresis import HysteresisBuffer


class TestBasics:
    def test_it_pauses_at_the_high_watermark(self):
        buffer = HysteresisBuffer(low=5, high=10)
        buffer.push(10)
        assert buffer.paused()

    def test_it_resumes_only_at_the_low_watermark(self):
        buffer = HysteresisBuffer(low=5, high=10)
        buffer.push(10)
        buffer.pop(3)  # down to 7, still above low
        assert buffer.paused()
        buffer.pop(3)  # down to 4, at or below low
        assert not buffer.paused()


class TestFlapping:
    def test_a_narrow_band_chatters_on_oscillation(self):
        buffer = HysteresisBuffer(low=9, high=10)
        buffer.push(10)
        for _ in range(20):
            buffer.pop(1)
            buffer.push(1)
        assert buffer.flips() == 41

    def test_a_wide_band_absorbs_the_same_oscillation(self):
        buffer = HysteresisBuffer(low=5, high=10)
        buffer.push(10)
        for _ in range(20):
            buffer.pop(1)
            buffer.push(1)
        assert buffer.flips() == 1


class TestRefusals:
    def test_low_at_or_above_high_is_refused(self):
        with pytest.raises(Invalid):
            HysteresisBuffer(low=10, high=10)

    def test_a_negative_push_is_refused(self):
        with pytest.raises(Invalid):
            HysteresisBuffer(low=1, high=5).push(-1)

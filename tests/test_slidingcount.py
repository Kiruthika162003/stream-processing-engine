from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.slidingcount import SlidingCount


class TestTheWindow:
    def test_it_holds_the_last_n_events(self):
        window = SlidingCount(capacity=3, aggregate="sum")
        for value in (10, 20, 30, 40):
            window.add(value)
        assert window.result() == 90

    def test_the_running_sum_is_incremental(self):
        window = SlidingCount(capacity=2, aggregate="sum")
        window.add(5)
        verdict = window.add(7)
        assert "window 12 in constant work" in verdict
        verdict = window.add(3)
        assert "evicted 5" in verdict
        assert window.result() == 10

    def test_count_reports_the_buffer_size(self):
        window = SlidingCount(capacity=3, aggregate="count")
        window.add(1)
        window.add(1)
        assert window.result() == 2

    def test_the_moving_average_uses_the_window(self):
        window = SlidingCount(capacity=3, aggregate="sum")
        for value in (10, 20, 30):
            window.add(value)
        assert window.moving_average() == 20.0


class TestRefusals:
    def test_a_non_invertible_aggregate_is_refused(self):
        with pytest.raises(Invalid) as caught:
            SlidingCount(capacity=3, aggregate="max")
        assert "you cannot un-see a maximum" in str(caught.value)

    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            SlidingCount(capacity=0, aggregate="sum")

    def test_an_empty_window_has_no_result(self):
        with pytest.raises(Invalid):
            SlidingCount(capacity=3, aggregate="sum").result()

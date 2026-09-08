from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.queueing import mean_queue_length, mean_wait


class TestHockeyStick:
    def test_the_wait_explodes_near_full_utilization(self):
        assert round(mean_wait(0.5, 1), 2) == 1.0
        assert round(mean_wait(0.9, 1), 2) == 9.0
        assert round(mean_wait(0.99, 1), 2) == 99.0

    def test_the_queue_length_follows_the_same_curve(self):
        assert mean_queue_length(0.5) == 1.0
        assert mean_queue_length(0.9) == pytest.approx(9.0)

    def test_an_idle_server_has_no_queue(self):
        assert mean_queue_length(0.0) == 0.0

    def test_the_wait_scales_with_service_time(self):
        assert mean_wait(0.9, 10) == pytest.approx(90.0)


class TestRefusals:
    def test_full_utilization_is_refused(self):
        with pytest.raises(Invalid):
            mean_queue_length(1.0)

    def test_a_negative_utilization_is_refused(self):
        with pytest.raises(Invalid):
            mean_queue_length(-0.1)

    def test_a_nonpositive_service_time_is_refused(self):
        with pytest.raises(Invalid):
            mean_wait(0.5, 0)

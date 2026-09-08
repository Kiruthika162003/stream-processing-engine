from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.slowstart import (
    CONGESTION_AVOIDANCE,
    SLOW_START,
    CongestionControl,
)


class TestSlowStart:
    def test_the_window_doubles_to_the_threshold_in_log_rounds(self):
        cc = CongestionControl(cwnd=1, ssthresh=64)
        windows = []
        rounds = 0
        while cc.phase() == SLOW_START:
            cc.on_ack()
            windows.append(cc.cwnd)
            rounds += 1
        assert windows == [2, 4, 8, 16, 32, 64]
        assert rounds == 6

    def test_reaching_the_threshold_switches_phase(self):
        cc = CongestionControl(cwnd=32, ssthresh=64)
        cc.on_ack()  # to 64
        assert cc.phase() == CONGESTION_AVOIDANCE


class TestCongestionAvoidance:
    def test_the_window_grows_by_one_per_ack(self):
        cc = CongestionControl(cwnd=64, ssthresh=64)
        cc.on_ack()
        cc.on_ack()
        assert cc.cwnd == 66


class TestLoss:
    def test_a_loss_halves_the_threshold_and_restarts_slow_start(self):
        cc = CongestionControl(cwnd=64, ssthresh=64)
        cc.on_loss()
        assert cc.ssthresh == 32
        assert cc.cwnd == 1
        assert cc.phase() == SLOW_START


class TestRefusals:
    def test_a_nonpositive_window_is_refused(self):
        with pytest.raises(Invalid):
            CongestionControl(cwnd=0, ssthresh=64)

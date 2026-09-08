from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.phiaccrual import PhiAccrual


def _regular() -> tuple[PhiAccrual, float]:
    detector = PhiAccrual()
    now = 0.0
    for _ in range(10):
        now += 100
        detector.heartbeat(now)
    return detector, now


def _erratic() -> tuple[PhiAccrual, float]:
    detector = PhiAccrual()
    now = 0.0
    for interval in (50, 150, 60, 140, 40, 160, 70, 130, 55, 145):
        now += interval
        detector.heartbeat(now)
    return detector, now


class TestOnTime:
    def test_an_on_time_gap_barely_raises_phi(self):
        detector, now = _regular()
        assert detector.phi(now + 100) < 1.0

    def test_a_late_gap_raises_phi_sharply(self):
        detector, now = _regular()
        assert detector.phi(now + 300) > 8.0


class TestAdaptivity:
    def test_the_erratic_node_is_judged_gentler_for_the_same_silence(self):
        regular, r_now = _regular()
        erratic, e_now = _erratic()
        regular_phi = regular.phi(r_now + 300)
        erratic_phi = erratic.phi(e_now + 300)
        assert erratic_phi < regular_phi
        assert 3.0 < erratic_phi < 8.0

    def test_suspect_thresholds_on_phi(self):
        detector, now = _regular()
        assert not detector.suspect(now + 100, threshold=8.0)
        assert detector.suspect(now + 300, threshold=8.0)


class TestRefusals:
    def test_too_few_heartbeats_is_refused(self):
        detector = PhiAccrual()
        detector.heartbeat(0)
        with pytest.raises(Invalid):
            detector.phi(100)

    def test_a_backward_heartbeat_is_refused(self):
        detector = PhiAccrual()
        detector.heartbeat(100)
        with pytest.raises(Invalid):
            detector.heartbeat(50)

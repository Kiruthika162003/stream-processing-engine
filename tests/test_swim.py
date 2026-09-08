from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.swim import (
    ALIVE,
    ALIVE_INDIRECT,
    SUSPECT,
    DirectOnlyDetector,
    SwimDetector,
)


class TestDirectOnly:
    def test_a_congested_path_falsely_suspects_a_live_node(self):
        detector = DirectOnlyDetector()
        assert detector.verdict(direct_ack=False) == SUSPECT

    def test_a_direct_ack_is_alive(self):
        assert DirectOnlyDetector().verdict(direct_ack=True) == ALIVE


class TestSwim:
    def test_an_indirect_ack_rescues_the_live_node(self):
        detector = SwimDetector(indirect_k=3)
        verdict = detector.verdict(
            direct_ack=False, indirect_acks=(False, True, False)
        )
        assert verdict == ALIVE_INDIRECT

    def test_all_probes_failing_together_is_suspect(self):
        detector = SwimDetector(indirect_k=3)
        verdict = detector.verdict(
            direct_ack=False, indirect_acks=(False, False, False)
        )
        assert verdict == SUSPECT

    def test_a_direct_ack_skips_the_indirect_round(self):
        detector = SwimDetector(indirect_k=3)
        assert detector.verdict(direct_ack=True, indirect_acks=()) == ALIVE


class TestRefusals:
    def test_a_zero_indirect_count_is_refused(self):
        with pytest.raises(Invalid):
            SwimDetector(indirect_k=0)

    def test_a_wrong_probe_count_is_refused(self):
        detector = SwimDetector(indirect_k=3)
        with pytest.raises(Invalid):
            detector.verdict(direct_ack=False, indirect_acks=(True,))

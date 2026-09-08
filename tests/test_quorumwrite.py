from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.quorumwrite import QuorumConfig


class TestTheOverlapInvariant:
    def test_a_valid_majority_quorum_holds(self):
        config = QuorumConfig(
            replicas=5, write_quorum=3, read_quorum=3
        )
        assert config.tolerates_failures() == 2

    def test_non_overlapping_quorums_are_refused(self):
        with pytest.raises(Invalid) as caught:
            QuorumConfig(
                replicas=5, write_quorum=2, read_quorum=2
            )
        assert "return a stale read that looks" in str(
            caught.value
        )

    def test_an_out_of_range_quorum_is_refused(self):
        with pytest.raises(Invalid):
            QuorumConfig(
                replicas=3, write_quorum=5, read_quorum=2
            )


class TestLatency:
    def test_the_wait_is_the_kth_fastest_not_the_slowest(self):
        config = QuorumConfig(
            replicas=5, write_quorum=3, read_quorum=3
        )
        verdict = config.write_latency([10, 90, 20, 15, 100])
        assert "quorum write waits 20 (the 3th fastest)" in verdict
        assert "not 100 (the slowest)" in verdict
        assert "buys the 80 tick difference" in verdict

    def test_a_latency_count_mismatch_is_refused(self):
        config = QuorumConfig(
            replicas=5, write_quorum=3, read_quorum=3
        )
        with pytest.raises(Invalid):
            config.write_latency([10, 20])


class TestTheNote:
    def test_the_overlap_note_explains_freshness(self):
        config = QuorumConfig(
            replicas=5, write_quorum=3, read_quorum=3
        )
        note = config.overlap_note()
        assert "overlap by 1 replica(s)" in note
        assert "a read always sees the latest write" in note

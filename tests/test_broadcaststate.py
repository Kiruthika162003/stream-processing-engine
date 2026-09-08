from __future__ import annotations

import pytest

from rill.broadcaststate import BroadcastState
from rill.errors import Invalid


def state() -> BroadcastState:
    return BroadcastState(partitions=4)


class TestBroadcast:
    def test_an_update_reaches_every_partition(self):
        chosen = state()
        verdict = chosen.broadcast_update(
            "block-country", "XX"
        )
        assert "broadcast to all 4 partition(s) in order" in (
            verdict
        )
        for partition in range(4):
            assert "block-country = XX" in chosen.read(
                partition, "block-country"
            )

    def test_an_unset_rule_reads_as_unset(self):
        chosen = state()
        assert "not set" in chosen.read(0, "ghost")

    def test_an_out_of_range_partition_is_refused(self):
        with pytest.raises(Invalid):
            state().read(9, "rule")

    def test_a_partitionless_job_is_refused(self):
        with pytest.raises(Invalid):
            BroadcastState(partitions=0)


class TestTheReadOnlyRule:
    def test_a_partition_write_is_refused_as_divergence(self):
        chosen = state()
        with pytest.raises(Invalid) as caught:
            chosen.partition_write(0, "rule", "value")
        assert "seen by one partition and no other" in str(
            caught.value
        )

    def test_the_consistency_check_confirms_one_view(self):
        chosen = state()
        chosen.broadcast_update("a", "1")
        chosen.broadcast_update("b", "2")
        check = chosen.consistency_check()
        assert "2 rule(s) replicated identically across 4" in (
            check
        )
        assert "no partition holds a different view" in check

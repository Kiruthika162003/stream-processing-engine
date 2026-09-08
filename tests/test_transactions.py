from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.transactions import TransactionalSession


def session() -> TransactionalSession:
    built = TransactionalSession(epoch=1)
    built.begin()
    return built


class TestTheBracket:
    def test_records_and_offset_land_together(self):
        chosen = session()
        chosen.stage("out-1")
        chosen.stage("out-2")
        verdict = chosen.commit(new_offset=10)
        assert verdict == (
            "2 record(s) and offset 10 landed together; no "
            "partial lie possible"
        )
        assert chosen.committed_output == ["out-1", "out-2"]

    def test_the_abort_leaves_the_offset_for_the_retry(self):
        chosen = session()
        chosen.stage("out-1")
        verdict = chosen.abort()
        assert (
            "1 staged record(s) rolled back, offset stays at 0"
        ) in verdict
        assert chosen.committed_output == []

    def test_the_offset_moves_with_the_writes_only(self):
        chosen = session()
        chosen.commit(new_offset=5)
        with pytest.raises(Invalid):
            chosen.commit(new_offset=5)


class TestTheFence:
    def test_the_zombie_is_refused_at_begin(self):
        chosen = TransactionalSession(epoch=1)
        chosen.fence(new_epoch=2)
        with pytest.raises(Halted) as caught:
            chosen.begin()
        assert "through the back door" in str(caught.value)

    def test_the_mid_flight_zombie_is_refused_at_commit(self):
        chosen = session()
        chosen.stage("out-1")
        chosen.fence(new_epoch=2)
        with pytest.raises(Halted) as caught:
            chosen.commit(new_offset=10)
        assert "the fence doing its one job" in str(
            caught.value
        )
        assert chosen.committed_output == []

    def test_fences_only_rise(self):
        chosen = session()
        chosen.fence(new_epoch=3)
        with pytest.raises(Invalid):
            chosen.fence(new_epoch=2)

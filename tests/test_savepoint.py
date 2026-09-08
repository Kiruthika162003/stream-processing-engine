from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.savepoint import Savepoint, UpgradeGate, round_trip_drill


def saved_v1() -> Savepoint:
    return Savepoint(
        schema_version=1, operator_state={"count:a": 7}
    )


class TestTheGate:
    def test_equal_versions_resume_clean(self):
        gate = UpgradeGate(expects_version=1)
        state, note = gate.resume(saved_v1())
        assert state == {"count:a": 7}
        assert note == "resumed clean at schema v1"

    def test_one_behind_runs_the_declared_migration(self):
        gate = UpgradeGate(
            expects_version=2,
            migrations={1: "keys unchanged"},
        )
        state, note = gate.resume(saved_v1())
        assert state == {"count:a": 7}
        assert note == "migrated v1 -> v2: keys unchanged"

    def test_the_gate_does_not_improvise(self):
        gate = UpgradeGate(expects_version=2)
        with pytest.raises(Invalid) as caught:
            gate.resume(saved_v1())
        assert "does not improvise state transforms" in str(
            caught.value
        )

    def test_skipping_rungs_is_refused_with_the_ladder(self):
        gate = UpgradeGate(expects_version=3)
        with pytest.raises(Invalid) as caught:
            gate.resume(saved_v1())
        message = str(caught.value)
        assert "v1 -> v2 -> v3" in message
        assert "never been written" in message or (
            "never written" in message
        )

    def test_resuming_backward_invents_amnesia(self):
        gate = UpgradeGate(expects_version=1)
        newer = Savepoint(schema_version=5, operator_state={})
        with pytest.raises(Invalid) as caught:
            gate.resume(newer)
        assert "invents amnesia" in str(caught.value)


class TestTheRoundTrip:
    def test_the_resumed_job_agrees_to_the_count(self):
        story = round_trip_drill()
        assert "agree to the count" in story
        assert "DIVERGED" not in story

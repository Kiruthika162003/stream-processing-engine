from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.rollback import DeployRollback


def incident() -> DeployRollback:
    return DeployRollback(
        deploy_position=8400,
        detection_position=9100,
        savepoint_position=8300,
    )


class TestTheGate:
    def test_the_predating_savepoint_is_safe(self):
        assert incident().gate() == (
            "savepoint at 8300 predates the deploy; safe to "
            "restore"
        )

    def test_the_postdating_savepoint_rolls_corruption_forward(self):
        bad = DeployRollback(
            deploy_position=8400,
            detection_position=9100,
            savepoint_position=8600,
        )
        with pytest.raises(Invalid) as caught:
            bad.gate()
        assert "the corruption forward" in str(caught.value)

    def test_time_still_runs_forward(self):
        with pytest.raises(Invalid):
            DeployRollback(
                deploy_position=100,
                detection_position=50,
                savepoint_position=10,
            )


class TestThePlan:
    def test_the_three_steps_carry_their_counts(self):
        plan = incident().plan()
        assert "1. restore the savepoint at 8300" in plan
        assert "800 event(s) to reprocess" in plan
        assert "correcting 700 poisoned event(s)" in plan

    def test_the_blast_statement_prevents_the_anomaly(self):
        statement = incident().blast_statement()
        assert statement.startswith(
            "events 8400 through 9100 were recomputed"
        )
        assert "as an anomaly" in statement

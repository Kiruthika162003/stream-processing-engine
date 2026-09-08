from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.savepointmigrate import SavepointMigrator


def migrator() -> SavepointMigrator:
    built = SavepointMigrator(operator_version=3)
    built.register(1, lambda s: {**s, "v2_field": 0})
    built.register(2, lambda s: {**s, "v3_field": "new"})
    return built


class TestResume:
    def test_matching_formats_resume_in_place(self):
        state, note = migrator().resume(3, {"count": 5})
        assert note == "resumed in place; formats match"
        assert state == {"count": 5}

    def test_the_old_savepoint_migrates_forward(self):
        state, note = migrator().resume(1, {"count": 5})
        assert state == {
            "count": 5,
            "v2_field": 0,
            "v3_field": "new",
        }
        assert "migrated v1 -> v3 through 2 step(s)" in note

    def test_a_newer_savepoint_is_refused(self):
        with pytest.raises(Invalid) as caught:
            migrator().resume(9, {})
        assert "reads bytes it cannot understand" in str(
            caught.value
        )

    def test_a_missing_migration_is_refused_before_start(self):
        built = SavepointMigrator(operator_version=3)
        built.register(2, lambda s: s)
        with pytest.raises(Invalid) as caught:
            built.resume(1, {})
        assert "passes every liveness check while producing" in (
            str(caught.value)
        )


class TestRegistration:
    def test_a_downward_migration_is_a_rollback_in_disguise(self):
        built = SavepointMigrator(operator_version=3)
        with pytest.raises(Invalid) as caught:
            built.register(3, lambda s: s)
        assert "rollback pretending to be a resume" in str(
            caught.value
        )

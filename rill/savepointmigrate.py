"""Savepoint migration: the state format changed, and the old savepoint must follow.

An operator's saved state has a layout, and when the operator
changes, a resume from an old savepoint reads bytes in a shape
the new code no longer understands, which is a crash on
startup at the worst time, right after a deploy. The migrator
makes state format a versioned thing like everything else: a
savepoint carries its schema version, resume checks it against
the operator's, and a compatible gap is migrated forward
field by field while an incompatible gap is refused before the
job starts rather than corrupting silently after it does. The
migration is forward-only and recorded, because a savepoint
migrated down to an older format is a rollback pretending to
be a resume, and the one thing worse than a crashed job is a
running job quietly reading half-migrated state, which passes
every liveness check while producing wrong answers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.errors import Invalid

Migration = Callable[[dict], dict]


@dataclass
class SavepointMigrator:
    operator_version: int
    migrations: dict[int, Migration] = field(
        default_factory=dict
    )
    applied: list[str] = field(default_factory=list)

    def register(
        self, from_version: int, migration: Migration
    ) -> None:
        if from_version >= self.operator_version:
            raise Invalid(
                f"migration from v{from_version} is not "
                "forward; a savepoint migrated down is a "
                "rollback pretending to be a resume"
            )
        self.migrations[from_version] = migration

    def resume(
        self, savepoint_version: int, state: dict
    ) -> tuple[dict, str]:
        if savepoint_version == self.operator_version:
            return state, "resumed in place; formats match"
        if savepoint_version > self.operator_version:
            raise Invalid(
                f"savepoint v{savepoint_version} is newer than "
                f"operator v{self.operator_version}; resuming "
                "into older code reads bytes it cannot understand"
            )
        current = dict(state)
        version = savepoint_version
        while version < self.operator_version:
            migration = self.migrations.get(version)
            if migration is None:
                raise Invalid(
                    f"no migration from v{version}; refused "
                    "before the job starts, because a running "
                    "job reading half-migrated state passes "
                    "every liveness check while producing wrong "
                    "answers"
                )
            current = migration(current)
            self.applied.append(
                f"v{version} -> v{version + 1}"
            )
            version += 1
        return current, (
            f"migrated v{savepoint_version} -> "
            f"v{self.operator_version} through "
            f"{len(self.applied)} step(s)"
        )

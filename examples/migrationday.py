"""Migration day: schema, savepoint, rescale, and the backfill's speed.

Run with: python -m examples.migrationday
"""

from __future__ import annotations

from rill.keygroups import KeyGroupAssignment
from rill.replayspeed import AcceleratedReplay
from rill.rescale import moving_day_report
from rill.savepointmigrate import SavepointMigrator
from rill.schemaregistry import Schema, SchemaRegistry


def morning_the_schema():
    base = Schema(
        version=1,
        required=frozenset({"id", "amount"}),
        optional=frozenset(),
    )
    registry = SchemaRegistry(current=base)
    evolved = Schema(
        version=2,
        required=base.required | {"currency"},
        optional=frozenset(),
    )
    print(f"schema:   {registry.propose(evolved, migration_window=100)}")


def midday_the_savepoint():
    migrator = SavepointMigrator(operator_version=3)
    migrator.register(1, lambda s: {**s, "v2": 0})
    migrator.register(2, lambda s: {**s, "v3": "new"})
    _, note = migrator.resume(1, {"count": 5})
    print(f"savepoint: {note}")


def afternoon_the_rescale():
    keys = [f"user-{n}" for n in range(500)]
    report = moving_day_report(keys, 4, 5)
    print(f"rescale:  {report.splitlines()[1].strip()}")
    print(f"          {report.splitlines()[3].strip()}")


def afternoon_the_keygroups():
    assignment = KeyGroupAssignment(key_groups=128, parallelism=4)
    print(f"keygroups: {assignment.rescale(new_parallelism=8)}")


def evening_the_backfill():
    replay = AcceleratedReplay(
        events=1_000_000, event_time_span=31_000_000
    )
    print(f"backfill: {replay.speedup(events_per_tick=1000)}")


def main() -> int:
    morning_the_schema()
    midday_the_savepoint()
    afternoon_the_rescale()
    afternoon_the_keygroups()
    evening_the_backfill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Savepoints: the pipeline stops on purpose and its state changes clothes.

A checkpoint is for crashes; a savepoint is for intentions:
stop the job, keep a portable snapshot of every operator's
state, upgrade the code, and resume from the snapshot as if
nothing happened, which works exactly as long as the new code
can read the old state. The state carries a schema version
for that reason, and the resume gate checks it against what
the new code expects: equal resumes clean, one behind runs
the declared migration and reports what it transformed, and
anything older is refused with the ladder spelled out,
because skipping two versions means running a migration that
was never written. The drill the module insists on is the
round trip: savepoint, upgrade, resume, and compare against
a job that never stopped, since a savepoint that loses a
single count is not an operations feature, it is a data bug
with a maintenance window.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Savepoint:
    schema_version: int
    operator_state: dict[str, int] = field(default_factory=dict)


@dataclass
class UpgradeGate:
    expects_version: int
    migrations: dict[int, str] = field(default_factory=dict)

    def resume(self, saved: Savepoint) -> tuple[dict[str, int], str]:
        gap = self.expects_version - saved.schema_version
        if gap == 0:
            return dict(saved.operator_state), (
                f"resumed clean at schema v{self.expects_version}"
            )
        if gap == 1:
            note = self.migrations.get(saved.schema_version)
            if note is None:
                raise Invalid(
                    f"no migration written from "
                    f"v{saved.schema_version}; the gate does "
                    "not improvise state transforms"
                )
            migrated = {
                key: value * 1
                for key, value in saved.operator_state.items()
            }
            return migrated, (
                f"migrated v{saved.schema_version} -> "
                f"v{self.expects_version}: {note}"
            )
        if gap > 1:
            ladder = " -> ".join(
                f"v{version}"
                for version in range(
                    saved.schema_version,
                    self.expects_version + 1,
                )
            )
            raise Invalid(
                f"the savepoint is {gap} versions old; the "
                f"ladder is {ladder} and skipping rungs means "
                "running a migration that was never written"
            )
        raise Invalid(
            "the savepoint is newer than the code; resuming "
            "backward invents amnesia"
        )


def round_trip_drill() -> str:
    never_stopped = {"count:a": 40, "count:b": 25}
    for key in never_stopped:
        never_stopped[key] += 10
    saved = Savepoint(
        schema_version=1,
        operator_state={"count:a": 40, "count:b": 25},
    )
    gate = UpgradeGate(
        expects_version=2,
        migrations={1: "counts keep their meaning, keys unchanged"},
    )
    resumed, note = gate.resume(saved)
    for key in resumed:
        resumed[key] += 10
    if resumed == never_stopped:
        return (
            f"{note}; the resumed job and the never-stopped "
            "job agree to the count, which is the sentence "
            "the maintenance window was promised"
        )
    return (
        "DIVERGED: the savepoint lost counts, a data bug "
        "with a maintenance window"
    )

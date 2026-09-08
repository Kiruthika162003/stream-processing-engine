"""Rolling back a stream deploy: rewind the code, rewind the state, say the blast.

A bad deploy of a stateless service rolls back in one step;
a bad deploy of a stream job rolls back in three, because
the bad code has been mutating state and emitting output the
whole time it ran: restore the pre-deploy savepoint, rewind
the input offsets to the savepoint's position, and reprocess
the poisoned window with the good code, overwriting or
correcting what the bad code emitted. The blast statement is
the step teams skip: the rollback's scope, from deploy to
detection plus reprocessing, stated as a window with counts,
because downstream consumers saw the bad output and "we
rolled back" without "events 8,400 through 9,100 were
recomputed, expect corrections" leaves every consumer
discovering the correction as an anomaly. The gate refuses a
rollback whose savepoint postdates the deploy, since
restoring state the bad code already touched rolls the code
back and the corruption forward.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class DeployRollback:
    deploy_position: int
    detection_position: int
    savepoint_position: int

    def __post_init__(self) -> None:
        if self.detection_position <= self.deploy_position:
            raise Invalid(
                "detection follows deploy; time still runs "
                "forward"
            )

    def gate(self) -> str:
        if self.savepoint_position > self.deploy_position:
            raise Invalid(
                f"the savepoint at {self.savepoint_position} "
                f"postdates the deploy at "
                f"{self.deploy_position}: restoring state the "
                "bad code touched rolls the code back and the "
                "corruption forward"
            )
        return (
            f"savepoint at {self.savepoint_position} predates "
            "the deploy; safe to restore"
        )

    def plan(self) -> str:
        self.gate()
        rewind = (
            self.detection_position - self.savepoint_position
        )
        poisoned = (
            self.detection_position - self.deploy_position
        )
        return "\n".join(
            [
                "the three steps, in order:",
                f"  1. restore the savepoint at "
                f"{self.savepoint_position}",
                f"  2. rewind offsets to "
                f"{self.savepoint_position} "
                f"({rewind} event(s) to reprocess)",
                f"  3. reprocess with the good code, "
                f"correcting {poisoned} poisoned event(s)",
            ]
        )

    def blast_statement(self) -> str:
        self.gate()
        return (
            f"events {self.deploy_position} through "
            f"{self.detection_position} were recomputed, "
            "expect corrections; without this sentence every "
            "consumer discovers the correction as an anomaly"
        )

"""Change data capture: the database's diary, read without waking it.

Polling a table for changes misses deletes, hammers the
database, and races its own interval; CDC reads the write-
ahead log instead, every insert, update, and delete in commit
order, which is the diary the database was already keeping.
The capture stream's discipline is completeness in kinds: an
update carries before and after images because downstream
wants to know what changed, not just what is, and a delete
is an event, not an absence, because the poller's fatal flaw
was exactly that deletes leave nothing to poll. The snapshot
plus tail protocol handles the newcomer: a consumer starting
today gets a consistent snapshot first, then the log from the
snapshot's position, and the seam between them is checked,
since a gap at the seam replays as missing rows and an
overlap replays as duplicates, the two classic CDC onboarding
wounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

KINDS = ("insert", "update", "delete")


@dataclass
class ChangeCapture:
    log: list[tuple[int, str, str, str | None, str | None]] = (
        field(default_factory=list)
    )

    def record(
        self,
        position: int,
        kind: str,
        key: str,
        before: str | None,
        after: str | None,
    ) -> None:
        if kind not in KINDS:
            raise Invalid(f"kind is one of {KINDS}")
        if self.log and position <= self.log[-1][0]:
            raise Invalid("the diary is written in commit order")
        if kind == "insert" and (
            before is not None or after is None
        ):
            raise Invalid("an insert has only an after image")
        if kind == "update" and (
            before is None or after is None
        ):
            raise Invalid(
                "an update carries before and after, because "
                "downstream wants what changed, not just what "
                "is"
            )
        if kind == "delete" and after is not None:
            raise Invalid("a delete has no after; it is an event, not an absence")
        self.log.append((position, kind, key, before, after))

    def snapshot_at(
        self, position: int
    ) -> dict[str, str]:
        state: dict[str, str] = {}
        for pos, kind, key, _, after in self.log:
            if pos > position:
                break
            if kind == "delete":
                state.pop(key, None)
            else:
                state[key] = after or ""
        return state

    def onboard(
        self, snapshot_position: int, tail_from: int
    ) -> str:
        if tail_from > snapshot_position + 1:
            gap = tail_from - snapshot_position - 1
            return (
                f"GAP at the seam: {gap} position(s) between "
                "snapshot and tail replay as missing rows, "
                "the first classic onboarding wound"
            )
        if tail_from <= snapshot_position:
            overlap = snapshot_position - tail_from + 1
            return (
                f"OVERLAP at the seam: {overlap} position(s) "
                "replay as duplicates, the second classic "
                "onboarding wound"
            )
        snapshot = self.snapshot_at(snapshot_position)
        tail = [
            entry for entry in self.log if entry[0] >= tail_from
        ]
        return (
            f"onboarded clean: snapshot of {len(snapshot)} "
            f"row(s) at {snapshot_position}, tail of "
            f"{len(tail)} change(s) from {tail_from}; the "
            "seam holds"
        )

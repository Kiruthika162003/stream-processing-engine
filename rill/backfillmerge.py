"""Backfill and live, merged: two streams of the same truth, no double-count.

Repairing history while serving the present means two streams
carrying the same events, the live one arriving now and the
backfill one replaying the past, and their overlap is a
landmine: an event both streams deliver, counted once by the
live pipeline and again by the backfill, inflates exactly the
metric the backfill was meant to fix. The merger uses the one
watertight rule, a position boundary: the backfill owns
everything up to the cutover position, live owns everything
after, and an event's stream membership is decided by its
position against the boundary, not by which stream happened
to carry it. Events from the wrong side of the boundary are
dropped as already-counted, named in the audit, because the
backfill that silently double-counts is worse than the gap it
repaired, and the whole operation's justification is the
audit reading zero double-counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class BackfillMerge:
    cutover_position: int
    counted: set[int] = field(default_factory=set)
    dropped_backfill: list[int] = field(default_factory=list)
    dropped_live: list[int] = field(default_factory=list)

    def from_backfill(self, position: int) -> str:
        if position >= self.cutover_position:
            self.dropped_live.append(position)
            return (
                f"backfill event at {position} dropped: past "
                "the cutover, live owns it"
            )
        return self._count(position, "backfill")

    def from_live(self, position: int) -> str:
        if position < self.cutover_position:
            self.dropped_backfill.append(position)
            return (
                f"live event at {position} dropped: before the "
                "cutover, backfill owns it"
            )
        return self._count(position, "live")

    def _count(self, position: int, stream: str) -> str:
        if position in self.counted:
            raise Invalid(
                f"position {position} counted twice; the "
                "boundary rule was bypassed"
            )
        self.counted.add(position)
        return f"{stream} event at {position} counted"

    def audit(self) -> str:
        overlap = set(self.dropped_backfill) & set(
            self.dropped_live
        )
        return (
            f"{len(self.counted)} event(s) counted once, "
            f"{len(self.dropped_backfill)} live drops before "
            f"cutover, {len(self.dropped_live)} backfill drops "
            f"after; {len(overlap)} double-count(s), and the "
            "whole operation is justified by that last number "
            "being zero"
        )

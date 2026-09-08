"""Pause and resume: the consumer steps out and leaves a bookmark, not a mess.

Maintenance needs consumers stopped, and the two wrong ways
are famous: killing the process mid-batch leaves half-applied
work for the crash machinery to untangle, and stopping intake
while keeping the assignment starves the partition without
telling anyone. The pause protocol is explicit: finish the
in-flight batch, commit the bookmark, announce paused with
the position, and hold the assignment so no rebalance fires
for a planned absence, because a rebalance is the group
paying for what a bookmark could have covered. Resume reads
the bookmark and reports the gap it must catch up, and the
overdue check watches the pause itself: a pause outliving
its declared window is an incident wearing a maintenance
label, and the check strips the label at the deadline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class PausableConsumer:
    name: str
    position: int = 0
    paused_at: int | None = None
    pause_deadline: int | None = None
    in_flight: int = 0
    log: list[str] = field(default_factory=list)

    def consume(self, count: int) -> None:
        if self.paused_at is not None:
            raise Invalid(f"{self.name} is paused; not a mess, a bookmark")
        if count < 1:
            raise Invalid("consuming nothing moves nothing")
        self.in_flight = count

    def finish_batch(self) -> None:
        self.position += self.in_flight
        self.in_flight = 0

    def pause(self, now: int, window: int) -> str:
        if self.in_flight:
            self.finish_batch()
            note = "in-flight batch finished first, "
        else:
            note = ""
        self.paused_at = now
        self.pause_deadline = now + window
        self.log.append(f"paused at position {self.position}")
        return (
            f"{self.name} paused: {note}bookmark at "
            f"{self.position}, assignment held so no rebalance "
            "fires for a planned absence"
        )

    def resume(self, stream_head: int) -> str:
        if self.paused_at is None:
            raise Invalid(f"{self.name} is not paused")
        gap = stream_head - self.position
        self.paused_at = None
        self.pause_deadline = None
        return (
            f"{self.name} resumes from {self.position}, "
            f"{gap} event(s) to catch up; the bookmark held"
        )

    def overdue_check(self, now: int) -> str:
        if self.paused_at is None:
            return f"{self.name} is running"
        if now <= self.pause_deadline:
            remaining = self.pause_deadline - now
            return (
                f"{self.name} paused with {remaining} tick(s) "
                "left in its window"
            )
        overdue = now - self.pause_deadline
        return (
            f"{self.name} pause is {overdue} tick(s) past its "
            "window: an incident wearing a maintenance label, "
            "and the label comes off now"
        )

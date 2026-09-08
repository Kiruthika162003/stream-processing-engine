"""Catch-up planning: the backfill and the live stream share one pipe.

After an outage the pipeline owes two workloads at once, the
backlog and the still-arriving present, and the split of
capacity between them is a policy pretending to be an
accident. Give everything to the backlog and live latency
craters for hours; give the backlog the leftovers and it
drains at a rate that rounds to never. The planner does the
arithmetic on the only three numbers involved, backlog size,
arrival rate, and total capacity, and prints the frontier:
for each capacity split, the catch-up time and the live lag
during it, so the incident channel picks a row instead of an
adjective. The impossible case is stated as such: capacity
below the arrival rate cannot catch up under any split, and
the plan says buy capacity or shed load, since a frontier
with no feasible rows is not a plan, it is a menu from a
closed kitchen.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class CatchupPlan:
    backlog: int
    arrival_rate: int
    capacity: int

    def __post_init__(self) -> None:
        if self.backlog < 1:
            raise Invalid("no backlog, no catch-up problem")
        if self.arrival_rate < 1 or self.capacity < 1:
            raise Invalid("rates must be positive")

    def row(self, backlog_share: int) -> str:
        if not 0 < backlog_share < 100:
            raise Invalid("the split is a percentage strictly between")
        to_backlog = self.capacity * backlog_share // 100
        to_live = self.capacity - to_backlog
        if to_backlog < 1:
            return (
                f"{backlog_share}%: the backlog gets a rate "
                "that rounds to never"
            )
        if to_live < self.arrival_rate:
            live_growth = self.arrival_rate - to_live
            note = (
                f"live lag grows {live_growth} per tick while "
                "catching up"
            )
        else:
            note = "live stays current"
        ticks = -(-self.backlog // to_backlog)
        return (
            f"{backlog_share}%: caught up in {ticks} tick(s), "
            f"{note}"
        )

    def frontier(self) -> str:
        if self.capacity <= self.arrival_rate:
            return (
                f"capacity {self.capacity} against arrivals "
                f"{self.arrival_rate}: no split catches up; "
                "buy capacity or shed load, because a frontier "
                "with no feasible rows is a menu from a closed "
                "kitchen"
            )
        lines = [
            "the frontier; the incident channel picks a row, "
            "not an adjective:"
        ]
        for share in (25, 50, 75):
            lines.append(f"  {self.row(share)}")
        return "\n".join(lines)

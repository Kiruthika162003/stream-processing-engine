"""Tiered log storage: the head on fast disk, the history in the object store.

A log's economics split at an age boundary: recent segments
serve every live consumer and belong on local disk, old
segments serve the occasional backfill and belong in the
object store at a tenth the price, and the tiering is honest
as long as the read path admits the difference instead of
averaging it. A read lands in the hot tier at disk speed or
in the cold tier at object-store speed, and the consumer
whose position drifts past the boundary crosses from one
world to the other mid-catchup, which the crossing report
names, because a backfill that suddenly runs five times
slower has not regressed, it has aged into the cold tier,
and the oncall who knows that reads a graph while the one
who does not files a bug. The offload rule is age plus a
safety margin behind the slowest consumer, since offloading
a segment a live consumer still needs converts its lag from
a number into a cliff.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

HOT_TICKS = 1
COLD_TICKS = 5


@dataclass
class TieredLog:
    offload_age: int
    head: int = 0
    boundary: int = 0
    reads_hot: int = 0
    reads_cold: int = 0
    crossings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.offload_age < 1:
            raise Invalid("the hot tier needs an age span")

    def append(self, count: int = 1) -> None:
        if count < 1:
            raise Invalid("appending nothing moves nothing")
        self.head += count

    def offload(self, slowest_consumer: int) -> str:
        target = min(
            self.head - self.offload_age, slowest_consumer
        )
        if target <= self.boundary:
            return (
                f"boundary holds at {self.boundary}; nothing "
                "old enough, or the slowest consumer still "
                "needs it"
            )
        moved = target - self.boundary
        self.boundary = target
        return (
            f"{moved} segment position(s) offloaded, boundary "
            f"now {self.boundary}; behind the slowest consumer "
            "on purpose, because offloading what a live "
            "consumer needs converts lag into a cliff"
        )

    def read(self, consumer: str, position: int) -> str:
        if position >= self.head:
            raise Invalid(f"{position} is past the head")
        if position >= self.boundary:
            self.reads_hot += 1
            return f"{consumer}: hot read, {HOT_TICKS} tick(s)"
        self.reads_cold += 1
        return (
            f"{consumer}: cold read, {COLD_TICKS} tick(s); "
            "aged, not regressed"
        )

    def crossing_report(
        self, consumer: str, position: int
    ) -> str:
        if position < self.boundary:
            note = (
                f"{consumer} is in the cold tier, "
                f"{self.boundary - position} position(s) from "
                "the crossing; the backfill runs slower here "
                "and has not regressed, it has aged"
            )
        else:
            note = (
                f"{consumer} is in the hot tier, serving at "
                "disk speed"
            )
        self.crossings.append(note)
        return note

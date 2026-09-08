"""Little's law: the queue's three numbers were never independent.

Occupancy equals arrival rate times residence time, always,
for any stable system, no assumptions about distributions or
burstiness, which makes it the one formula worth carrying
into a capacity meeting. The sizer applies it in both useful
directions: given the arrival rate and the delay the SLA
tolerates, the buffer that suffices is their product, and a
bigger buffer is not safety, it is stored delay, a queue
that hides its backlog inside its capacity; given an
observed occupancy and rate, the residence time falls out,
and a buffer running at high occupancy is not almost-full,
it is a delay meter reading near its maximum. The law's
violation detector is free: occupancy persistently above
rate times residence means the system is not stable, which
is Little's polite word for falling behind.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class LittleSizer:
    arrival_rate: int

    def __post_init__(self) -> None:
        if self.arrival_rate < 1:
            raise Invalid("the law needs a positive rate")

    def buffer_for_delay(self, tolerable_delay: int) -> str:
        if tolerable_delay < 1:
            raise Invalid("the SLA tolerates at least one tick")
        size = self.arrival_rate * tolerable_delay
        return (
            f"rate {self.arrival_rate} x delay "
            f"{tolerable_delay} = buffer {size}; anything "
            "bigger is not safety, it is stored delay"
        )

    def delay_from_occupancy(self, occupancy: int) -> str:
        if occupancy < 0:
            raise Invalid("occupancy cannot be negative")
        delay = occupancy / self.arrival_rate
        return (
            f"occupancy {occupancy} at rate "
            f"{self.arrival_rate} means {delay:.1f} tick(s) "
            "of residence; a full buffer is a delay meter "
            "reading near its maximum"
        )

    def stability_check(
        self, occupancy: int, expected_residence: int
    ) -> str:
        implied = self.arrival_rate * expected_residence
        if occupancy <= implied:
            return (
                f"stable: occupancy {occupancy} within the "
                f"law's {implied}"
            )
        return (
            f"UNSTABLE: occupancy {occupancy} exceeds rate "
            f"times residence ({implied}); the system is not "
            "stable, which is Little's polite word for "
            "falling behind"
        )

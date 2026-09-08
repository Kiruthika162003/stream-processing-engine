"""The watermark: a promise about the past that only ever moves forward.

A watermark at time T is the processor asserting that events
with event time at or before T have, to the best of its
knowledge, arrived, and every downstream decision that fires a
window or drops a straggler leans on that assertion. The
bounded strategy is the honest workhorse: track the highest
event time seen, subtract a lateness bound, and never let the
result move backward, because a watermark that retreats
un-fires windows that already told someone their answer. The
bound is a bet, not a fact: set it small and stragglers are
declared late while still in flight, set it large and every
window waits on events that already arrived, and the ledger
counts both costs so the bet can be re-sized from evidence
rather than from the last incident's adrenaline.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid
from rill.events import Event


@dataclass
class BoundedWatermark:
    lateness_bound: int
    highest_event_time: int = -1
    current: int = -1
    late_events: int = 0
    advances: int = 0

    def __post_init__(self) -> None:
        if self.lateness_bound < 0:
            raise Invalid(
                "a negative bound promises the future has "
                "already arrived"
            )

    def observe(self, event: Event) -> str:
        if self.current >= 0 and event.event_time <= self.current:
            self.late_events += 1
            return (
                f"{event.key}@{event.event_time} is LATE: the "
                f"watermark already passed {self.current} and "
                "a promise about the past does not reopen"
            )
        self.highest_event_time = max(self.highest_event_time, event.event_time)
        proposed = self.highest_event_time - self.lateness_bound
        if proposed > self.current:
            self.current = proposed
            self.advances += 1
            return (
                f"watermark advances to {self.current}; events "
                f"at or before it are now presumed arrived"
            )
        return f"{event.key}@{event.event_time} observed, watermark holds"

    def would_be_late(self, event_time: int) -> bool:
        return 0 <= self.current >= event_time

    def ledger(self) -> str:
        return (
            f"watermark {self.current} after "
            f"{self.advances} advance(s), bound "
            f"{self.lateness_bound}, {self.late_events} "
            "late event(s); the bound is a bet, and these are "
            "the numbers that re-size it"
        )

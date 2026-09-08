"""Sliding count-based windows: the last N events, not the last N seconds.

Some questions are about the last hundred events regardless of
how long they took, the moving average of the last hundred
trades, the error rate over the last thousand requests, and a
count-based window answers them where a time-based window
cannot, because it holds a fixed number of events and slides
by discarding the oldest as each new one arrives. The
implementation trap is recomputing the aggregate over the
whole buffer on every event, which is linear per event and
quadratic over the stream; the module keeps a running
aggregate and updates it incrementally, adding the new event
and subtracting the evicted one, so each event costs constant
work. The subtraction is only valid for invertible
aggregates, sum and count yes, min and max no, because you
cannot un-see the maximum when it slides out without keeping
more state, and the module refuses the incremental path for a
non-invertible aggregate rather than producing a wrong moving
maximum that looks plausible until the true max slides away.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from rill.errors import Invalid

INVERTIBLE = ("sum", "count")


@dataclass
class SlidingCount:
    capacity: int
    aggregate: str
    buffer: deque = field(default_factory=deque)
    running_sum: int = 0

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise Invalid("the window holds at least one event")
        if self.aggregate not in INVERTIBLE:
            raise Invalid(
                f"{self.aggregate} is not invertible; you "
                "cannot un-see a maximum that slid out, so the "
                "incremental path would produce a plausible "
                "wrong answer"
            )
        self.buffer = deque(maxlen=self.capacity)

    def add(self, value: int) -> str:
        evicted = None
        if len(self.buffer) == self.capacity:
            evicted = self.buffer[0]
        self.buffer.append(value)
        if evicted is not None:
            self.running_sum -= evicted
        self.running_sum += value
        return (
            f"added {value}"
            + (
                f", evicted {evicted}"
                if evicted is not None
                else ""
            )
            + f"; window {self.result()} in constant work"
        )

    def result(self) -> int:
        if not self.buffer:
            raise Invalid("an empty window has no result")
        if self.aggregate == "count":
            return len(self.buffer)
        return self.running_sum

    def moving_average(self) -> float:
        if not self.buffer:
            raise Invalid("no events for an average")
        return self.running_sum / len(self.buffer)

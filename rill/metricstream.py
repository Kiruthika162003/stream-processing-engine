"""Operator metrics: percentiles from a ring, honest about its size.

Every operator wants its latency distribution, and storing
every measurement is a pipeline watching itself drown; the
ring buffer keeps the last N and computes percentiles over
what it holds, which is the standard bargain and fine as long
as the report says so. The percentile arithmetic here uses
the nearest-rank method because it never invents values: p99
is an actual observed latency, not an interpolation between
two, and when someone grep's the logs for that exact number
they will find the event that produced it, which is worth
more than a smoother curve. The tail warning is the piece
dashboards omit: a ring of 100 cannot see a 1-in-1000 event
except by luck, so the report prints the slowest event the
ring ever evicted, tracked separately, because the worst
latency your window can show and the worst latency you have
served are different numbers and the pager fires on the
second.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class LatencyRing:
    capacity: int
    ring: list[int] = field(default_factory=list)
    cursor: int = 0
    total_seen: int = 0
    worst_ever: int = -1

    def __post_init__(self) -> None:
        if self.capacity < 10:
            raise Invalid(
                "a ring under 10 cannot even pretend to "
                "percentiles"
            )

    def observe(self, latency: int) -> None:
        if latency < 0:
            raise Invalid("latency cannot be negative")
        self.total_seen += 1
        self.worst_ever = max(self.worst_ever, latency)
        if len(self.ring) < self.capacity:
            self.ring.append(latency)
        else:
            self.ring[self.cursor] = latency
            self.cursor = (self.cursor + 1) % self.capacity

    def percentile(self, rank: int) -> int:
        if not self.ring:
            raise Invalid("no observations")
        if not 1 <= rank <= 100:
            raise Invalid("percentiles run 1 to 100")
        ordered = sorted(self.ring)
        index = max(
            0, (rank * len(ordered) + 99) // 100 - 1
        )
        return ordered[index]

    def report(self) -> str:
        p50 = self.percentile(50)
        p99 = self.percentile(99)
        window = len(self.ring)
        line = (
            f"p50 {p50}, p99 {p99} over the last {window} of "
            f"{self.total_seen} observation(s); nearest-rank, "
            "so every number is an event you can grep for"
        )
        if self.worst_ever > max(self.ring):
            line += (
                f"; worst ever served {self.worst_ever}, "
                "outside this window, and the pager fires on "
                "that number, not the window's"
            )
        return line

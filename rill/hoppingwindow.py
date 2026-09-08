"""Hopping windows: the sliding window's overlap, counted honestly.

A hopping window is a sliding window by another name, size
larger than hop so consecutive windows overlap, and the
overlap is the feature and the cost at once: an event in the
overlap belongs to multiple windows, so it is counted in each,
and the sum of all window counts exceeds the event count by
exactly the overlap factor. Teams misread this as
double-counting and file a bug; it is correct, and the module
makes the overlap factor explicit so the analyst expects the
inflation instead of investigating it. The factor is size
over hop rounded up, the number of windows any single event
falls into, and the module refuses a hop larger than the size,
which would leave gaps that events fall through uncounted, the
opposite and worse error. The memory cost is the same factor:
holding size-over-hop windows open at once, which is the
storage a hopping window trades for its smooth output.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class HoppingWindows:
    size: int
    hop: int
    counts: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.size < 1 or self.hop < 1:
            raise Invalid("size and hop are positive")
        if self.hop > self.size:
            raise Invalid(
                f"hop {self.hop} exceeds size {self.size}: "
                "gaps between windows let events fall through "
                "uncounted, worse than overlap"
            )

    def overlap_factor(self) -> int:
        return -(-self.size // self.hop)

    def windows_for(self, event_time: int) -> list[int]:
        windows = []
        first_start = (
            (event_time - self.size) // self.hop + 1
        ) * self.hop
        start = max(0, first_start)
        while start <= event_time:
            windows.append(start)
            start += self.hop
        return windows

    def add(self, event_time: int) -> str:
        windows = self.windows_for(event_time)
        for start in windows:
            self.counts[start] = self.counts.get(start, 0) + 1
        return (
            f"event at {event_time} counted in "
            f"{len(windows)} window(s): {windows}"
        )

    def inflation_note(self, events: int) -> str:
        total_counts = sum(self.counts.values())
        return (
            f"{events} event(s) produced {total_counts} window "
            f"count(s), inflated by the {self.overlap_factor()}x "
            "overlap factor; correct, not double-counting, and "
            "expecting it beats investigating it"
        )

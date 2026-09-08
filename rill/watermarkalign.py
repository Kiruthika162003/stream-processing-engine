"""Watermark alignment: the far-ahead partition pauses so state stops growing.

Reading several partitions at once, one can race far ahead of
another in event time, and an operator that joins or windows
across them must hold state for the fast partition until the slow
one reaches the same time, so the buffered state grows with the
drift between them, not with the throughput. Left alone a
partition that is minutes ahead pins minutes of the other side's
records in memory. Watermark alignment caps the drift with a
maximum: once a partition's watermark runs more than maxDrift
past the slowest partition's, the source stops reading it until
the slow one catches up, bounding the buffer at roughly maxDrift
worth of skew at the cost of idling the fast partition. This
module tracks per-partition watermarks, names the partitions that
have run past the allowed drift and must pause, and reports the
current spread, so the maxDrift is a visible dial between a
bounded buffer and a fast reader held back rather than a memory
graph that climbs until the join falls over.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class AlignmentGroup:
    max_drift: int
    _watermark: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_drift <= 0:
            raise Invalid("max drift must be positive")

    def advance(self, partition: str, watermark: int) -> None:
        prior = self._watermark.get(partition)
        if prior is not None and watermark < prior:
            raise Invalid(f"{partition} watermark went backward")
        self._watermark[partition] = watermark

    def slowest(self) -> int:
        if not self._watermark:
            raise Invalid("no partitions yet")
        return min(self._watermark.values())

    def spread(self) -> int:
        if not self._watermark:
            raise Invalid("no partitions yet")
        return max(self._watermark.values()) - min(self._watermark.values())

    def paused(self) -> list[str]:
        floor = self.slowest()
        return sorted(
            p
            for p, w in self._watermark.items()
            if w - floor > self.max_drift
        )

    def may_read(self, partition: str) -> bool:
        if partition not in self._watermark:
            raise Invalid(f"unknown partition {partition}")
        return self._watermark[partition] - self.slowest() <= self.max_drift

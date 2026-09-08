"""Adaptive replica selection: send the read to the replica that has been fastest.

Reading from any of several replicas, round-robin spreads the
load evenly and ignores the one fact that matters, that the
replicas are not equally fast right now. A replica in the middle
of a garbage-collection pause, a slow disk, or a compaction is
temporarily much slower than its peers, and round-robin keeps
sending it its full share of reads, so a fraction of every
client's requests inherit that replica's stall for no reason.
Adaptive selection tracks each replica's recent latency with an
exponential moving average and sends each read to the replica
with the lowest current estimate, so a replica that slows down
stops receiving traffic until it recovers and speeds back up,
and the slow one's stall is routed around rather than shared.
The estimate has to decay, which is what the moving average
gives it, so a replica that was slow and is now fast is tried
again rather than blacklisted forever. This module keeps a
per-replica latency average, picks the current fastest, and lets
the estimate age, so the difference between routing around a slow
replica and dealing it its share regardless is a measured gap in
served latency.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid
from rill.ewma import Ewma


@dataclass
class ReplicaSelector:
    alpha: float = 0.3
    _latency: dict[str, Ewma] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha <= 1.0:
            raise Invalid("alpha must be in (0, 1]")

    def observe(self, replica: str, latency: float) -> None:
        if latency < 0:
            raise Invalid("latency cannot be negative")
        self._latency.setdefault(replica, Ewma(self.alpha)).update(latency)

    def estimate(self, replica: str) -> float:
        if replica not in self._latency:
            raise Invalid(f"no observations for {replica}")
        return self._latency[replica].corrected()

    def pick(self) -> str:
        if not self._latency:
            raise Invalid("no replicas observed yet")
        return min(self._latency, key=lambda r: self._latency[r].corrected())

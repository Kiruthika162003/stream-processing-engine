"""Partitions: parallelism by key, and the skew that eats it.

A partitioned stream promises parallelism: N partitions, N
workers, N times the throughput. The promise holds exactly
until one key gets famous, because a key's events must stay
in one partition to keep their order, so the partition
holding the hot key does the work while its siblings idle,
and the pipeline's throughput quietly becomes the throughput
of one partition wearing N's name plate. The partitioner
routes by stable hash so a key's home never moves between
restarts, the census measures balance as the ratio of the
busiest partition to the mean, and the skew verdict names
the hot keys outright, because the fixes, splitting the key,
salting it, or accepting it, are all key-level decisions and
a partition-level number cannot make them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_bucket
from rill.errors import Invalid


@dataclass
class Partitioner:
    partitions: int
    counts: list[int] = field(default_factory=list)
    by_key: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.partitions < 1:
            raise Invalid("a stream needs at least one partition")
        if not self.counts:
            self.counts = [0] * self.partitions

    def route(self, key: str) -> int:
        if not key:
            raise Invalid("a keyless event routes nowhere")
        home = stable_bucket(key, self.partitions)
        self.counts[home] += 1
        self.by_key[key] = self.by_key.get(key, 0) + 1
        return home

    def balance(self) -> float:
        total = sum(self.counts)
        if total == 0:
            raise Invalid("no events routed; balance is a rumor")
        mean = total / self.partitions
        return max(self.counts) / mean

    def skew_verdict(self) -> str:
        ratio = self.balance()
        total = sum(self.counts)
        if ratio <= 1.5:
            return (
                f"balanced at {ratio:.1f}x the mean across "
                f"{self.partitions} partition(s); the promise "
                "of parallelism holds"
            )
        hot = sorted(
            self.by_key.items(),
            key=lambda item: -item[1],
        )[:2]
        named = ", ".join(
            f"{key} ({100 * count // total}%)"
            for key, count in hot
        )
        return (
            f"SKEWED: the busiest partition runs at "
            f"{ratio:.1f}x the mean, and throughput is one "
            f"partition wearing {self.partitions}'s name "
            f"plate; hot key(s): {named}, and the fixes, "
            "splitting, salting, or accepting, are key-level "
            "decisions"
        )

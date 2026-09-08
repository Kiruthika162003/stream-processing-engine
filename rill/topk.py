"""Heavy hitters in fixed memory: the famous keys, found without a census.

Counting every key exactly needs memory proportional to the
keys, and a stream has more keys than any budget; the
space-saving sketch keeps counters for only k candidates and
still finds the famous ones, by a bargain with error: when a
stranger arrives and the table is full, it evicts the
smallest counter and inherits its count plus one, so every
counter is an overestimate by at most what the evicted ghost
had. The sketch therefore reports each hitter with its error
bar, count and maximum overcount together, and the guarantee
worth stating is the honest one: any key whose true count
exceeds the smallest counter is certainly in the table, so
the sketch never misses a truly heavy hitter, it only
sometimes flatters a light one, and knowing which failure is
possible is most of knowing how to read the table.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SpaceSaving:
    capacity: int
    counts: dict[str, int] = field(default_factory=dict)
    overcounts: dict[str, int] = field(default_factory=dict)
    evictions: int = 0

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise Invalid("a sketch needs at least one counter")

    def offer(self, key: str) -> None:
        if not key:
            raise Invalid("a keyless event counts as nothing")
        if key in self.counts:
            self.counts[key] += 1
            return
        if len(self.counts) < self.capacity:
            self.counts[key] = 1
            self.overcounts[key] = 0
            return
        victim = min(
            self.counts, key=lambda held: (self.counts[held], held)
        )
        inherited = self.counts.pop(victim)
        self.overcounts.pop(victim)
        self.counts[key] = inherited + 1
        self.overcounts[key] = inherited
        self.evictions += 1

    def hitters(self, top: int) -> list[str]:
        ranked = sorted(
            self.counts,
            key=lambda key: (-self.counts[key], key),
        )[:top]
        return [
            f"{key}: {self.counts[key]} (overcount at most "
            f"{self.overcounts[key]})"
            for key in ranked
        ]

    def floor(self) -> int:
        if not self.counts:
            raise Invalid("an empty sketch has no floor")
        return min(self.counts.values())

    def reading_guide(self) -> str:
        return (
            f"{len(self.counts)} counter(s), floor "
            f"{self.floor()}, {self.evictions} eviction(s): "
            "any key truly above the floor is certainly here; "
            "the sketch never misses a heavy hitter, it only "
            "sometimes flatters a light one"
        )

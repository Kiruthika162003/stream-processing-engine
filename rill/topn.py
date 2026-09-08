"""Streaming top-N: the leaderboard that cannot see the whole board.

Keeping the top ten of a billion keys exactly needs every
key's count in memory, which a stream forbids, so the
approximate top-N keeps a bounded set of candidate counters
and admits the honest hazard: a key that was quiet early and
surged late can be missing from the candidate set at the
moment it should have entered the leaderboard, and no bounded
structure can promise otherwise. The tracker uses the
space-saving policy, when a new key arrives and the set is
full, it evicts the current minimum and gives the newcomer
that minimum's count plus one, which bounds the overcount and
guarantees the true top-N is present when the counter budget
exceeds the number of keys above the tail. The report states
its own uncertainty: entries carry a possible-overcount
because an evicted-and-returned key inherited counts it did
not earn, and a leaderboard that hides its error bars is a
leaderboard that will be quoted as exact.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SpaceSaving:
    capacity: int
    counters: dict[str, int] = field(default_factory=dict)
    overcount: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise Invalid("the leaderboard needs room for one")

    def observe(self, key: str) -> None:
        if key in self.counters:
            self.counters[key] += 1
            return
        if len(self.counters) < self.capacity:
            self.counters[key] = 1
            return
        victim = min(
            self.counters, key=lambda k: self.counters[k]
        )
        floor = self.counters.pop(victim)
        self.overcount.pop(victim, None)
        self.counters[key] = floor + 1
        self.overcount[key] = floor

    def top(self, n: int) -> list[tuple[str, int]]:
        return sorted(
            self.counters.items(),
            key=lambda item: (-item[1], item[0]),
        )[:n]

    def report(self, n: int) -> str:
        lines = [f"top {n} (approximate, error bars shown):"]
        for key, count in self.top(n):
            possible = self.overcount.get(key, 0)
            note = (
                f" (up to {possible} overcounted)"
                if possible
                else " (exact)"
            )
            lines.append(f"  {key}: {count}{note}")
        lines.append(
            "a leaderboard that hides its error bars gets "
            "quoted as exact"
        )
        return "\n".join(lines)

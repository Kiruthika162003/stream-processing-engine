"""State spillover: memory is for the working set, disk is for the biography.

Keyed state outgrows memory long before it outgrows disk, and
the spillover keeps the distinction honest: hot keys, touched
recently, live in memory at memory speed; cold keys spill to
disk and pay the disk's latency on their next visit, which
promotes them back. The accounting is the design: every access
is billed at its tier's price, the ledger splits time spent
by tier, and the working-set verdict compares the hot set the
policy kept against the keys the traffic actually revisited,
because a spill policy is a bet about the future and the only
way to grade a bet is against what happened. The failure
worth naming is thrash: a working set larger than memory
makes every access a promotion, disk speed with memory's
bookkeeping, and the ledger calls it before the latency graph
does.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

MEMORY_TICKS = 1
DISK_TICKS = 20


@dataclass
class SpillStore:
    memory_capacity: int
    hot: dict[str, int] = field(default_factory=dict)
    cold: dict[str, int] = field(default_factory=dict)
    recency: list[str] = field(default_factory=list)
    ticks_billed: int = 0
    promotions: int = 0
    hot_hits: int = 0

    def __post_init__(self) -> None:
        if self.memory_capacity < 1:
            raise Invalid("memory holds at least one key")

    def _touch(self, key: str) -> None:
        if key in self.recency:
            self.recency.remove(key)
        self.recency.append(key)

    def _make_room(self) -> None:
        while len(self.hot) >= self.memory_capacity:
            victim = self.recency.pop(0)
            self.cold[victim] = self.hot.pop(victim)

    def put(self, key: str, value: int) -> None:
        if not key:
            raise Invalid("state has keys")
        if key in self.hot:
            self.hot[key] = value
            self._touch(key)
            self.ticks_billed += MEMORY_TICKS
            return
        self.cold.pop(key, None)
        self._make_room()
        self.hot[key] = value
        self._touch(key)
        self.ticks_billed += MEMORY_TICKS

    def get(self, key: str) -> tuple[int | None, str]:
        if key in self.hot:
            self.ticks_billed += MEMORY_TICKS
            self.hot_hits += 1
            self._touch(key)
            return self.hot[key], "memory speed"
        if key in self.cold:
            self.ticks_billed += DISK_TICKS
            self.promotions += 1
            value = self.cold.pop(key)
            self._make_room()
            self.hot[key] = value
            self._touch(key)
            return value, (
                "disk latency paid, promoted back to memory"
            )
        return None, "never seen"

    def thrash_check(self) -> str:
        touches = self.hot_hits + self.promotions
        if touches == 0:
            raise Invalid("no reads to grade the bet against")
        promotion_share = 100 * self.promotions // touches
        if promotion_share >= 50:
            return (
                f"THRASH: {promotion_share}% of reads promoted "
                "from disk; the working set is larger than "
                "memory, so every access runs at disk speed "
                "with memory's bookkeeping, and this ledger "
                "calls it before the latency graph does"
            )
        return (
            f"{promotion_share}% of reads promoted; the hot "
            f"set is holding, {self.ticks_billed} tick(s) "
            "billed across both tiers"
        )

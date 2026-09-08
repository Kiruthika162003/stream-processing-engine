"""The timer heap: millions of pending timers, and the one due next.

A stream with a timer per key, a session expiry, a scheduled
retry, a timeout, accumulates millions of pending timers, and
firing them needs the earliest-due one on every watermark
advance, which a linear scan cannot afford at that scale. A
min-heap keyed by fire time makes the next-due lookup constant
and insertion logarithmic, but the operation streams actually
stress is deletion, because a timer is far more often
cancelled, the session that got another event, than fired, and
a heap cannot delete an arbitrary element cheaply. The lazy
deletion policy is the standard answer and the module makes it
honest with a per-key generation: cancelling and rescheduling
both bump the key's generation, so every heap entry from an
older generation is a tombstone skipped at the top, holding
the live count to one entry per key even after the same key
has been rescheduled a thousand times. The first version
forgot the generation and fired a revived key twice, because
clearing a shared dead-mark resurrected the stale entry along
with the new one; the generation is what keeps the old entry
dead while the new one lives. Compaction watches the tombstone
ratio, the signal to rebuild that a size metric alone hides.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field


@dataclass
class TimerHeap:
    heap: list[tuple[int, int, str, int]] = field(
        default_factory=list
    )
    generation: dict[str, int] = field(default_factory=dict)
    live: set[str] = field(default_factory=set)
    sequence: int = 0

    def schedule(self, key: str, fire_time: int) -> None:
        gen = self.generation.get(key, 0) + 1
        self.generation[key] = gen
        self.live.add(key)
        heapq.heappush(
            self.heap, (fire_time, self.sequence, key, gen)
        )
        self.sequence += 1

    def cancel(self, key: str) -> str:
        self.generation[key] = self.generation.get(key, 0) + 1
        self.live.discard(key)
        return (
            f"{key} cancelled: its generation bumped so every "
            "outstanding entry is a tombstone, because a heap "
            "cannot delete an arbitrary element cheaply"
        )

    @property
    def live_count(self) -> int:
        return len(self.live)

    def fire_due(self, watermark: int) -> list[str]:
        fired = []
        while self.heap and self.heap[0][0] <= watermark:
            _, _, key, gen = heapq.heappop(self.heap)
            if (
                key in self.live
                and self.generation.get(key) == gen
            ):
                fired.append(key)
                self.live.discard(key)
        return fired

    def dead_ratio(self) -> float:
        if not self.heap:
            return 0.0
        tombstones = len(self.heap) - len(self.live)
        return tombstones / len(self.heap)

    def compaction_note(self) -> str:
        ratio = self.dead_ratio()
        if ratio >= 0.5:
            return (
                f"{ratio:.0%} tombstones: the heap spends its "
                "time skipping the dead, rebuild it; a size "
                "metric alone would hide this"
            )
        return (
            f"{ratio:.0%} tombstones, {self.live_count} live; "
            "healthy, no rebuild needed"
        )

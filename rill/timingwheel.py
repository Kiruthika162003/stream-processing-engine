"""Timing wheel: scheduling and expiring timers in constant time by bucketing on expiry.

A stream with millions of pending timers, one per session, per
retry, per timeout, needs to schedule a timer and fire the due
ones cheaply, and a min-heap does both in logarithmic time, which
at that scale and churn is real cost. A timing wheel does them in
constant time. It is a circular array of buckets, one per tick,
and a timer due in d ticks is dropped into the bucket d positions
ahead of the current one, a single indexed insert with no
comparison. Each tick advances the current position by one and
fires exactly the timers in the bucket it lands on, touching only
that bucket rather than searching a heap. The circular array wraps,
so a delay longer than the wheel is handled by recording how many
full revolutions remain and decrementing that count each time the
current position passes the bucket, firing only when it reaches
zero, which keeps the wheel small while still scheduling far-out
timers, the hierarchical idea in one level. The trade against the
heap is that the wheel's resolution and range are fixed by its
size and tick, where the heap handles any delay, but for the
bounded, high-churn timers a stream actually holds, constant-time
scheduling beats logarithmic. This module schedules by delay and
advances tick by tick, firing due timers, so the O(1) schedule and
single-bucket expiry are a measured behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class TimingWheel:
    slots: int
    _current: int = 0
    _buckets: list[list[tuple[int, str]]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.slots < 1:
            raise Invalid("wheel needs at least one slot")
        self._buckets = [[] for _ in range(self.slots)]

    def schedule(self, delay: int, item: str) -> None:
        if delay < 1:
            raise Invalid("delay must be at least one tick")
        slot = (self._current + delay) % self.slots
        rounds = delay // self.slots
        self._buckets[slot].append((rounds, item))

    def advance(self) -> list[str]:
        self._current = (self._current + 1) % self.slots
        fired: list[str] = []
        remaining: list[tuple[int, str]] = []
        for rounds, item in self._buckets[self._current]:
            if rounds == 0:
                fired.append(item)
            else:
                remaining.append((rounds - 1, item))
        self._buckets[self._current] = remaining
        return fired

    def pending(self) -> int:
        return sum(len(bucket) for bucket in self._buckets)

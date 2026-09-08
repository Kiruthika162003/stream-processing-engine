"""Leaky bucket: output smoothed to a constant rate, and the latency that costs.

The token bucket and the leaky bucket both limit a rate and they
shape traffic in opposite ways. A token bucket lets a burst
through all at once as long as it has saved tokens, so its output
is spiky up to the burst size. A leaky bucket queues arrivals and
drains them at a fixed rate no matter how they arrived, so its
output is perfectly smooth and its cost is latency: a burst that
lands in one instant leaves the bucket spread across many ticks,
and every item after the first waits in the queue for its turn to
leak. When the queue is full the overflow is dropped outright,
because the whole point is that the output rate is a hard ceiling
the bucket will not exceed to catch up. This module queues
arrivals up to a capacity, drops the overflow, and leaks at the
fixed rate, so the difference from a token bucket is a
measurement rather than an argument: the same burst that a token
bucket would emit in one tick this bucket meters out over the
several ticks its rate requires.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class LeakyBucket:
    rate: int
    capacity: int
    _queue: int = 0

    def __post_init__(self) -> None:
        if self.rate <= 0 or self.capacity <= 0:
            raise Invalid("rate and capacity must be positive")

    def arrive(self, count: int) -> int:
        if count < 0:
            raise Invalid("count cannot be negative")
        room = self.capacity - self._queue
        admitted = min(count, room)
        self._queue += admitted
        return count - admitted

    def leak(self) -> int:
        emitted = min(self.rate, self._queue)
        self._queue -= emitted
        return emitted

    def drain_ticks(self) -> int:
        return -(-self._queue // self.rate)

    def queued(self) -> int:
        return self._queue

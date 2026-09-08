"""Vegas concurrency limit: back off on the queue latency reveals, before a loss forces it.

AIMD grows the in-flight limit until a loss and then halves it, so
it deliberately overshoots the safe concurrency, drives the system
into queueing, and only retreats once packets drop, a sawtooth
that spends part of every cycle in the congested region it should
avoid. The Vegas approach reads congestion earlier, from latency
rather than loss. It tracks the smallest round-trip time it has
seen, the latency with no queue, and compares it to the current
round-trip time: when requests are queueing, the current time
exceeds the minimum, and the excess implies how many in-flight
requests are waiting rather than working. That estimated queue is
the signal. When it is below a low threshold there is spare
capacity and the limit nudges up to probe for more; when it climbs
above a high threshold the limit eases down, and in between it
holds. Because it reacts to the latency the queue creates rather
than to the loss the overflow eventually causes, it settles the
limit near the point of no queueing and stays there, without the
overshoot-and-halve cycle. The trade is that it depends on a
trustworthy minimum RTT and gentle latency signals, where loss is
unambiguous. This module runs the gradient update against measured
round-trip times, so the settle-without-overshoot behavior is a
measured limit.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class VegasLimiter:
    limit: int = 4
    low: int = 2
    high: int = 4
    _min_rtt: float | None = None

    def __post_init__(self) -> None:
        if self.limit < 1 or not 0 <= self.low <= self.high:
            raise Invalid("need limit >= 1 and 0 <= low <= high")

    def observe(self, rtt: float) -> int:
        if rtt <= 0:
            raise Invalid("rtt must be positive")
        if self._min_rtt is None or rtt < self._min_rtt:
            self._min_rtt = rtt
        estimated_queue = self.limit * (1 - self._min_rtt / rtt)
        if estimated_queue < self.low:
            self.limit += 1
        elif estimated_queue > self.high:
            self.limit = max(1, self.limit - 1)
        return self.limit

    def estimated_queue(self, rtt: float) -> float:
        if self._min_rtt is None:
            return 0.0
        return self.limit * (1 - self._min_rtt / rtt)

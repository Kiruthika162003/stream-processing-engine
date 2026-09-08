"""Hedged requests: a second copy for the slow tail, priced by where you set the delay.

A request that usually returns fast and occasionally stalls
drags the tail latency up, and hedging answers by sending a
second copy to another replica if the first has not returned
within a hedge delay, then taking whichever answers first. The
tail shrinks because the stalled request no longer has to finish;
the fast backup caps it. The cost is extra load, one duplicate
request for every hedge that fires, and where the hedge delay
sits decides whether that cost is worth it. Set the delay below
the median and nearly every request hedges, so the load roughly
doubles to shave a tail that was not the problem. Set it up at a
high percentile and only the genuinely slow requests hedge, so a
few percent more load buys back most of the tail. This module
computes, for a batch of primary latencies against a backup
latency and a hedge delay, the latency each request actually
served and the fraction that had to hedge, so the delay is a
measured trade between a smaller tail and more load rather than a
number picked from a blog post.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class Hedger:
    hedge_delay: int
    backup_latency: int

    def __post_init__(self) -> None:
        if self.hedge_delay < 0 or self.backup_latency < 0:
            raise Invalid("delays cannot be negative")

    def served(self, primary_latency: int) -> int:
        if primary_latency <= self.hedge_delay:
            return primary_latency
        return min(primary_latency, self.hedge_delay + self.backup_latency)

    def hedged(self, primary_latency: int) -> bool:
        return primary_latency > self.hedge_delay

    def batch(self, primaries: list[int]) -> dict[str, float]:
        if not primaries:
            raise Invalid("no latencies to summarize")
        served = sorted(self.served(p) for p in primaries)
        hedges = sum(1 for p in primaries if self.hedged(p))
        index = max(0, (99 * len(served)) // 100 - 1)
        return {
            "p99": served[index],
            "hedge_rate": hedges / len(primaries),
        }

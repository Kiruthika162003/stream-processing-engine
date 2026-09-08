"""Watermark lag: the gap between now and the time the pipeline believes in.

Processing lag measures how far behind the newest event a
consumer is; watermark lag measures something subtler and more
useful, how far the pipeline's notion of complete time trails
wall-clock now, and the two diverge in a way that matters. A
pipeline can be caught up on processing, its consumer at the
head of the log, and still have a watermark far behind now,
because the watermark waits for the slowest source and the
largest allowed lateness, so watermark lag is the true answer
to when will this window's results be final. The module
tracks watermark lag against a freshness SLA and distinguishes
its two causes, because they have different fixes: lag from a
large lateness bound is a deliberate correctness-latency
tradeoff the operator chose, while lag from a straggling
source is an incident, and reporting them as one number sends
the operator to change a config that was set correctly on
purpose.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class WatermarkLag:
    lateness_bound: int
    freshness_sla: int

    def __post_init__(self) -> None:
        if self.lateness_bound < 0 or self.freshness_sla < 1:
            raise Invalid(
                "a nonnegative bound and a positive SLA"
            )

    def lag(self, now: int, watermark: int) -> int:
        if watermark > now:
            raise Invalid("the watermark cannot lead wall clock")
        return now - watermark

    def diagnose(
        self, now: int, watermark: int, slowest_source: int
    ) -> str:
        lag = self.lag(now, watermark)
        if lag <= self.freshness_sla:
            return (
                f"watermark lag {lag} within the {self.freshness_sla} "
                "SLA; results finalize on time"
            )
        source_lag = now - slowest_source
        bound_share = self.lateness_bound
        if source_lag > bound_share:
            return (
                f"watermark lag {lag} over SLA, mostly from a "
                f"straggling source ({source_lag} behind): an "
                "incident, not the bound you set on purpose"
            )
        return (
            f"watermark lag {lag} over SLA, mostly from the "
            f"{self.lateness_bound} lateness bound: a "
            "correctness-latency tradeoff you chose, so shrink "
            "the bound only if you accept more late drops"
        )

"""Latency histograms: the average hides the tail that pages you.

Reporting average processing latency is worse than useless, it
is misleading, because the average of a latency distribution
sits below the median for the skewed shapes latency always has,
and the events that page an operator live in the 99th
percentile the average never mentions. The histogram keeps
bucketed counts and answers percentile queries, and the module
insists on the tail: a report that gives the mean without the
p99 is refused, because the two together tell a story the mean
alone inverts, a system with a fine average and a terrible p99
is a system failing its slowest one percent of requests, which
at scale is thousands of users. The bucket boundaries are
logarithmic on purpose, because latency spans orders of
magnitude and linear buckets waste all their resolution on the
fast requests nobody worries about while lumping the entire
slow tail into one final bucket that hides exactly the
variation worth seeing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

BUCKETS = (1, 10, 100, 1000, 10000)


@dataclass
class LatencyHistogram:
    counts: list[int] = field(
        default_factory=lambda: [0] * (len(BUCKETS) + 1)
    )
    total: int = 0
    sum_latency: int = 0

    def observe(self, latency: int) -> None:
        if latency < 0:
            raise Invalid("latency is nonnegative")
        self.total += 1
        self.sum_latency += latency
        for index, boundary in enumerate(BUCKETS):
            if latency <= boundary:
                self.counts[index] += 1
                return
        self.counts[-1] += 1

    def percentile(self, pct: int) -> int:
        if not 0 < pct <= 100:
            raise Invalid("a percentile is in (0, 100]")
        if self.total == 0:
            raise Invalid("no observations")
        target = self.total * pct / 100
        cumulative = 0
        for index, count in enumerate(self.counts):
            cumulative += count
            if cumulative >= target:
                if index < len(BUCKETS):
                    return BUCKETS[index]
                return BUCKETS[-1] * 10
        return BUCKETS[-1] * 10

    def mean(self) -> float:
        if self.total == 0:
            raise Invalid("no observations")
        return self.sum_latency / self.total

    def report(self) -> str:
        return (
            f"mean {self.mean():.0f}, p50 {self.percentile(50)}, "
            f"p99 {self.percentile(99)}; the mean without the "
            "p99 inverts the story, since a fine average with a "
            "terrible p99 fails the slowest one percent, "
            "thousands of users at scale"
        )

"""Watermark generation strategies: three ways to guess when the past is done.

The bounded-lateness watermark subtracts a fixed margin from
the max seen, which is one strategy among several, each fitting
a different stream. The percentile strategy sizes the margin
from the observed lateness distribution, tracking how late
events actually are and setting the bound to cover, say, the
99th percentile, so the margin adapts instead of being guessed
once and left wrong. The per-partition strategy generates a
watermark per input and takes the minimum, correct when
sources have independent lateness. The module refuses to
pretend one strategy fits all, because a stream with a stable
network wants a small fixed margin and a stream with bursty
mobile clients wants a percentile that breathes, and using the
fixed strategy on the bursty stream drops a tenth of the
events as late while using the percentile on the stable one
holds every window an extra second for stragglers that never
come. The strategy is a choice priced in the two errors it
trades between, late drops and holding delay.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class PercentileWatermark:
    coverage_percentile: int
    max_seen: int = -1
    lateness_samples: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 50 <= self.coverage_percentile <= 100:
            raise Invalid(
                "coverage is a percentile between 50 and 100"
            )

    def observe(self, event_time: int) -> None:
        lateness = max(0, self.max_seen - event_time)
        self.lateness_samples.append(lateness)
        self.max_seen = max(self.max_seen, event_time)

    def margin(self) -> int:
        if not self.lateness_samples:
            raise Invalid("no samples; the margin is a guess")
        ordered = sorted(self.lateness_samples)
        index = min(
            len(ordered) - 1,
            len(ordered) * self.coverage_percentile // 100,
        )
        return ordered[index]

    def watermark(self) -> int:
        return self.max_seen - self.margin()

    def adapts_note(self) -> str:
        return (
            f"margin {self.margin()} covers the "
            f"{self.coverage_percentile}th percentile of "
            f"{len(self.lateness_samples)} observed lateness(es); "
            "it breathes with the stream instead of being "
            "guessed once and left wrong"
        )


def strategy_advice(
    network_stability: str,
) -> str:
    if network_stability == "stable":
        return (
            "use a small fixed margin: a percentile strategy "
            "here holds every window an extra second for "
            "stragglers that never come"
        )
    if network_stability == "bursty":
        return (
            "use a percentile margin that breathes: a fixed "
            "margin here drops a tenth of the events as late"
        )
    raise Invalid(
        f"{network_stability} is not a stability class; the "
        "strategy is a choice, not a default"
    )

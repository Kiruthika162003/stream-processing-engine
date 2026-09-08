"""Consumer lag: the one number that says whether the stream is a stream.

Throughput flatters and latency percentiles confuse, but lag,
how far the consumer trails the head of the log, is the
number that decides everything: a pipeline with growing lag
is a batch job that has not admitted it yet. The tracker
takes arrival rate and drain rate per window and answers the
only question operations asks: are we catching up, holding,
or falling behind, and if catching up, when does the lag
reach zero, stated in ticks rather than optimism. The
falling-behind verdict refuses to soften: a drain rate below
the arrival rate has no catch-up date, and the report says
"never at these rates" in those words, because dashboards
that render that condition as a large number teach operators
to believe in large numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class LagTracker:
    lag: int
    history: list[tuple[int, int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.lag < 0:
            raise Invalid("lag below zero means reading the future")

    def observe_window(self, arrived: int, drained: int) -> str:
        if arrived < 0 or drained < 0:
            raise Invalid("rates cannot be negative")
        self.history.append((arrived, drained))
        self.lag = max(0, self.lag + arrived - drained)
        return f"lag {self.lag} after +{arrived}/-{drained}"

    def _recent_rates(self) -> tuple[float, float]:
        if not self.history:
            raise Invalid("no windows observed; lag is a rumor")
        recent = self.history[-3:]
        arrivals = sum(a for a, _ in recent) / len(recent)
        drains = sum(d for _, d in recent) / len(recent)
        return arrivals, drains

    def verdict(self) -> str:
        arrivals, drains = self._recent_rates()
        if self.lag == 0 and drains >= arrivals:
            return "caught up and holding; the stream is a stream"
        surplus = drains - arrivals
        if surplus <= 0:
            return (
                f"FALLING BEHIND: lag {self.lag} and growing "
                f"{-surplus:.0f} per window; there is no "
                "catch-up date, never at these rates, and a "
                "dashboard that renders this as a large number "
                "teaches operators to believe in large numbers"
            )
        windows = self.lag / surplus
        return (
            f"catching up: lag {self.lag}, surplus "
            f"{surplus:.0f} per window, caught up in "
            f"{windows:.0f} window(s); ticks, not optimism"
        )

    def batch_job_check(self) -> str:
        if len(self.history) < 4:
            return "too soon to accuse anyone"
        growth = [
            arrived > drained
            for arrived, drained in self.history[-4:]
        ]
        if all(growth):
            return (
                "four straight windows of growth: this "
                "pipeline is a batch job that has not admitted "
                "it yet"
            )
        return "still a stream, some weeks barely"

"""Replay speed: reprocessing a year of history should not take a year.

Recomputing a metric over historical data replays the log,
and the naive replay honors the original timing, sleeping
between events to reproduce the pace they arrived at, which
means reprocessing a year takes a year and the backfill
finishes after the question stopped mattering. Accelerated
replay strips the wall-clock waits and runs event time as
fast as the CPU allows, but the acceleration exposes a bug
that hid in production: code that secretly depended on wall
clock, a cache that expired on real seconds, a rate limiter
counting real time, behaves differently at speed, so the
accelerator flags operations that read wall time during a
replay as replay-unsafe, because a backfill that produces
different numbers than the original run is a backfill nobody
can trust, and the difference is always some hidden
dependence on the clock the replay just sped past.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class AcceleratedReplay:
    events: int
    event_time_span: int
    wall_clock_reads: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.events < 1 or self.event_time_span < 1:
            raise Invalid("a replay needs events over a span")

    def naive_wall_time(self) -> int:
        return self.event_time_span

    def accelerated_wall_time(self, events_per_tick: int) -> int:
        if events_per_tick < 1:
            raise Invalid("acceleration processes events per tick")
        return -(-self.events // events_per_tick)

    def speedup(self, events_per_tick: int) -> str:
        naive = self.naive_wall_time()
        fast = self.accelerated_wall_time(events_per_tick)
        ratio = naive / fast
        return (
            f"naive replay {naive} tick(s), accelerated "
            f"{fast} ({ratio:.0f}x); a year of history should "
            "not take a year to reprocess"
        )

    def flag_wall_clock(self, operation: str) -> str:
        self.wall_clock_reads.append(operation)
        return (
            f"{operation} read wall time during replay: "
            "replay-unsafe, because a backfill that differs "
            "from the original run is one nobody can trust"
        )

    def safety_report(self) -> str:
        if not self.wall_clock_reads:
            return (
                "replay-safe: nothing read wall time, so the "
                "accelerated numbers equal the original"
            )
        return (
            f"{len(self.wall_clock_reads)} replay-unsafe "
            f"operation(s): {', '.join(self.wall_clock_reads)}; "
            "each is a hidden dependence on the clock the "
            "replay sped past"
        )

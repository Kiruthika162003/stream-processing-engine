"""Log retention: the tail is falling off, and someone is standing on it.

A log retains a window of history and deletes from the tail,
and the deletion is routine until a consumer's lag exceeds
the retention span, at which point the log deletes events the
consumer has not read yet, silently, which the consumer
experiences as an offset gap and operations experiences as an
argument about whose fault it was. The margin tracker does
the one calculation that prevents the argument: retention
span minus current lag, in ticks, per consumer, published as
time-to-data-loss, and the escalation ladder is explicit,
comfortable, tightening, and critical with the deadline
attached, because "consumer B loses data in 40 ticks" gets a
fix deployed and "lag is elevated" gets a dashboard glance.
The gap event itself, when it happens, is recorded with both
numbers, what was lost and who was standing where, so the
postmortem opens with facts instead of archaeology.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class RetentionMargin:
    retention_span: int
    consumers: dict[str, int] = field(default_factory=dict)
    gap_events: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.retention_span <= 0:
            raise Invalid("a log that retains nothing is a pipe")

    def report_lag(self, consumer: str, lag: int) -> str:
        if lag < 0:
            raise Invalid("lag cannot be negative")
        self.consumers[consumer] = lag
        margin = self.retention_span - lag
        if margin <= 0:
            lost = -margin + 1
            self.gap_events.append(
                f"{consumer} lost {lost} tick(s) of data: lag "
                f"{lag} outran retention {self.retention_span}"
            )
            return (
                f"{consumer} GAP: the tail fell off under it, "
                f"roughly {lost} tick(s) of data gone; the "
                "postmortem opens with facts, not archaeology"
            )
        if margin <= self.retention_span // 10:
            return (
                f"{consumer} CRITICAL: data loss in {margin} "
                "tick(s) at current lag; this sentence gets a "
                "fix deployed"
            )
        if margin <= self.retention_span // 3:
            return (
                f"{consumer} tightening: {margin} tick(s) of "
                "margin left"
            )
        return f"{consumer} comfortable: margin {margin}"

    def board(self) -> str:
        if not self.consumers:
            raise Invalid("no consumers reporting")
        lines = ["time-to-data-loss, per consumer:"]
        for consumer in sorted(
            self.consumers,
            key=lambda name: self.consumers[name],
            reverse=True,
        ):
            margin = self.retention_span - self.consumers[consumer]
            state = (
                "GAP"
                if margin <= 0
                else f"{margin} tick(s) of margin"
            )
            lines.append(f"  {consumer}: {state}")
        if self.gap_events:
            lines.append(
                f"{len(self.gap_events)} gap event(s) on "
                "record with both numbers"
            )
        return "\n".join(lines)

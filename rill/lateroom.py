"""The late room: stragglers are routed, never deleted.

Dropping late events on the floor is the default in too many
pipelines, and the floor is where audit discrepancies live.
The late room is a side output with a policy: every event
that arrives behind the watermark is admitted with its
lateness measured, the room keeps a histogram of how late
late actually is, and the histogram is the single most useful
input to re-sizing the watermark bound, because "we drop some
stragglers" is a shrug while "88 percent of our late events
are under three ticks late" is a decision waiting to be
signed. The room supports two exits and both are deliberate:
reconcile, which hands a batch of stragglers to a correction
job with the affected windows named, and expire, which
abandons events past a patience horizon with a count, since
even honesty needs a horizon or the room becomes the leak.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid
from rill.events import Event
from rill.windows import Window, tumbling


@dataclass
class LateRoom:
    patience: int
    window_size: int
    held: list[tuple[Event, int]] = field(default_factory=list)
    expired: int = 0
    reconciled: int = 0

    def __post_init__(self) -> None:
        if self.patience <= 0 or self.window_size <= 0:
            raise Invalid(
                "the room needs positive patience and window "
                "size; even honesty needs a horizon"
            )

    def admit(self, event: Event, watermark: int) -> str:
        lateness = watermark - event.event_time
        if lateness < 0:
            raise Invalid(
                f"{event.key}@{event.event_time} is not late "
                f"against watermark {watermark}; the room is "
                "for stragglers, not commuters"
            )
        self.held.append((event, lateness))
        return (
            f"{event.key}@{event.event_time} admitted, "
            f"{lateness} tick(s) late"
        )

    def histogram(self) -> str:
        if not self.held:
            return "the room is empty; either on time or lying"
        buckets = {"1-3": 0, "4-10": 0, "11+": 0}
        for _, lateness in self.held:
            if lateness <= 3:
                buckets["1-3"] += 1
            elif lateness <= 10:
                buckets["4-10"] += 1
            else:
                buckets["11+"] += 1
        total = len(self.held)
        parts = [
            f"{label}: {count} ({100 * count // total}%)"
            for label, count in buckets.items()
        ]
        return (
            f"{total} straggler(s): {', '.join(parts)}; the "
            "input to re-sizing the bound, a decision waiting "
            "to be signed"
        )

    def reconcile(self) -> str:
        if not self.held:
            raise Invalid("nothing to reconcile")
        windows: set[Window] = {
            tumbling(event.event_time, self.window_size)
            for event, _ in self.held
        }
        count = len(self.held)
        self.reconciled += count
        self.held.clear()
        named = ", ".join(
            window.label() for window in sorted(
                windows, key=lambda w: w.start
            )
        )
        return (
            f"{count} straggler(s) handed to the correction "
            f"job; affected window(s): {named}"
        )

    def expire_impatient(self, watermark: int) -> str:
        doomed = [
            (event, lateness)
            for event, lateness in self.held
            if watermark - event.event_time > self.patience
        ]
        self.held = [
            entry for entry in self.held if entry not in doomed
        ]
        self.expired += len(doomed)
        return (
            f"{len(doomed)} abandoned past the patience "
            f"horizon of {self.patience}, {len(self.held)} "
            "still waiting; counted, because the floor is "
            "where audit discrepancies live"
        )

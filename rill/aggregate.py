"""Windowed aggregation: the pane accumulates, the watermark decides.

An aggregating window is a bet split in two: the pane
accumulates state as events arrive, in any order, and the
watermark decides when the answer is spoken. Firing early is
tempting and wrong twice over: an early answer changes when
stragglers land, and a changed answer downstream is a
retraction wearing an update's clothes. The aggregator keeps
one pane per key per window, folds events in as they come,
and speaks a pane's result only when the watermark passes the
window's end, at which point the pane is sealed: late events
for a sealed pane are counted and named rather than folded,
because silently folding them would reopen an answer someone
already acted on. The ledger reports panes fired, events
folded, and late events refused, the three numbers that
describe how well the watermark's bet fit this stream.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid
from rill.events import Event
from rill.watermark import BoundedWatermark
from rill.windows import Window, tumbling


@dataclass
class WindowedSum:
    window_size: int
    watermark: BoundedWatermark
    panes: dict[tuple[str, Window], int] = field(
        default_factory=dict
    )
    sealed: set[tuple[str, Window]] = field(default_factory=set)
    fired: list[str] = field(default_factory=list)
    refused_late: list[str] = field(default_factory=list)
    folded: int = 0

    def __post_init__(self) -> None:
        if self.window_size <= 0:
            raise Invalid("a window needs positive size")

    def feed(self, event: Event) -> list[str]:
        window = tumbling(event.event_time, self.window_size)
        slot = (event.key, window)
        notes = []
        if slot in self.sealed:
            self.refused_late.append(
                f"{event.key}@{event.event_time}"
            )
            notes.append(
                f"late for sealed {window.label()}: counted "
                "and named, never folded, because a sealed "
                "answer was already acted on"
            )
            return notes
        self.panes[slot] = self.panes.get(slot, 0) + event.value
        self.folded += 1
        self.watermark.observe(event)
        notes.extend(self._fire_ready())
        return notes

    def _fire_ready(self) -> list[str]:
        spoken = []
        for (key, window), total in sorted(
            self.panes.items(),
            key=lambda item: (item[0][1].end, item[0][0]),
        ):
            if window.end <= self.watermark.current:
                spoken.append(
                    f"{key} {window.label()} = {total}; the "
                    "watermark passed, the pane seals"
                )
                self.fired.append(f"{key}{window.label()}={total}")
                self.sealed.add((key, window))
                del self.panes[(key, window)]
        return spoken

    def ledger(self) -> str:
        return (
            f"{len(self.fired)} pane(s) fired, {self.folded} "
            f"event(s) folded, {len(self.refused_late)} late "
            f"refusal(s), {len(self.panes)} pane(s) still "
            "accumulating; how well the bet fit this stream"
        )

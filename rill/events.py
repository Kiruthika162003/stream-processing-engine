"""Events carry two clocks, and the processor only ever receives one order.

Every event in this package tells two stories about time: its
event time, when the source claims the thing happened, and its
arrival, when the processor actually saw it. The gap between
them is transit skew, and the whole discipline of stream
processing exists because that gap is neither zero nor
constant. A Tape is a recorded stream in arrival order, which
is the only order a processor ever truly receives; event-time
order is a reconstruction, available in hindsight and priced
accordingly. The disorder count measures how far the two
orders disagree, adjacent inversions in arrival order, because
"how out of order is this stream" deserves a number before
anyone sizes a watermark against it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass(frozen=True)
class Event:
    key: str
    value: int
    event_time: int
    arrival: int

    def __post_init__(self) -> None:
        if self.event_time < 0 or self.arrival < 0:
            raise Invalid(
                "both clocks start at zero; negative time is "
                "a bug wearing a timestamp"
            )
        if not self.key:
            raise Invalid("an event without a key routes nowhere")

    def skew(self) -> int:
        return self.arrival - self.event_time

    def line(self) -> str:
        return (
            f"{self.key}={self.value} happened at "
            f"{self.event_time}, seen at {self.arrival} "
            f"(skew {self.skew()})"
        )


@dataclass
class Tape:
    events: list[Event] = field(default_factory=list)

    def record(self, event: Event) -> None:
        if self.events and event.arrival < self.events[-1].arrival:
            raise Invalid(
                "arrival order is the one order the tape "
                "guarantees; a rewound arrival breaks the tape"
            )
        self.events.append(event)

    def in_arrival_order(self) -> list[Event]:
        return list(self.events)

    def in_event_time_order(self) -> list[Event]:
        return sorted(
            self.events,
            key=lambda event: (event.event_time, event.arrival),
        )

    def disorder(self) -> int:
        count = 0
        for before, after in zip(
            self.events, self.events[1:], strict=False
        ):
            if after.event_time < before.event_time:
                count += 1
        return count

    def max_skew(self) -> int:
        if not self.events:
            raise Invalid("an empty tape has no skew to report")
        return max(event.skew() for event in self.events)

    def report(self) -> str:
        if not self.events:
            return "empty tape; nothing happened, or nothing arrived"
        return (
            f"{len(self.events)} event(s), disorder "
            f"{self.disorder()}, max skew {self.max_skew()}; "
            "event-time order is a reconstruction, priced in "
            "hindsight"
        )

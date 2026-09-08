"""Stream joins: two rivers, one window, and the memory between them.

Joining streams is joining time: an order and its payment
match only if they occur within a tolerance of each other, so
the join buffers each side, probes the other side's buffer on
every arrival, and evicts what the tolerance has outgrown.
The buffers are the price and the tolerance is the knob:
widen it and the join catches more pairs while holding more
memory, narrow it and the buffers shrink while genuine pairs
miss each other and leak out the unmatched exits. The exits
are the honest part: a production join that only reports
matches is hiding its losses, so this one emits unmatched
left and unmatched right on eviction, named and countable,
because the order that never met its payment is precisely the
event somebody downstream is paid to worry about.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid
from rill.events import Event


@dataclass
class IntervalJoin:
    tolerance: int
    left_buffer: dict[str, list[Event]] = field(
        default_factory=dict
    )
    right_buffer: dict[str, list[Event]] = field(
        default_factory=dict
    )
    matches: list[str] = field(default_factory=list)
    matched_ids: set[tuple[str, str, int]] = field(
        default_factory=set
    )
    unmatched_left: list[str] = field(default_factory=list)
    unmatched_right: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.tolerance < 0:
            raise Invalid("a negative tolerance matches nothing")

    def _probe(
        self, event: Event, other: dict[str, list[Event]]
    ) -> list[Event]:
        candidates = other.get(event.key, [])
        return [
            held
            for held in candidates
            if abs(held.event_time - event.event_time)
            <= self.tolerance
        ]

    def feed_left(self, event: Event) -> list[str]:
        found = self._probe(event, self.right_buffer)
        notes = []
        for partner in found:
            pair = (
                f"{event.key}: left@{event.event_time} joins "
                f"right@{partner.event_time}"
            )
            self.matches.append(pair)
            self.matched_ids.add(
                ("left", event.key, event.event_time)
            )
            self.matched_ids.add(
                ("right", partner.key, partner.event_time)
            )
            notes.append(pair)
        self.left_buffer.setdefault(event.key, []).append(event)
        return notes

    def feed_right(self, event: Event) -> list[str]:
        found = self._probe(event, self.left_buffer)
        notes = []
        for partner in found:
            pair = (
                f"{event.key}: left@{partner.event_time} joins "
                f"right@{event.event_time}"
            )
            self.matches.append(pair)
            self.matched_ids.add(
                ("right", event.key, event.event_time)
            )
            self.matched_ids.add(
                ("left", partner.key, partner.event_time)
            )
            notes.append(pair)
        self.right_buffer.setdefault(event.key, []).append(event)
        return notes

    def evict(self, watermark: int) -> str:
        horizon = watermark - self.tolerance
        evicted_left = evicted_right = 0
        for key in list(self.left_buffer):
            keep = []
            for event in self.left_buffer[key]:
                if event.event_time < horizon:
                    evicted_left += 1
                    if (
                        "left",
                        event.key,
                        event.event_time,
                    ) not in self.matched_ids:
                        self.unmatched_left.append(
                            f"{event.key}@{event.event_time}"
                        )
                else:
                    keep.append(event)
            self.left_buffer[key] = keep
        for key in list(self.right_buffer):
            keep = []
            for event in self.right_buffer[key]:
                if event.event_time < horizon:
                    evicted_right += 1
                    if (
                        "right",
                        event.key,
                        event.event_time,
                    ) not in self.matched_ids:
                        self.unmatched_right.append(
                            f"{event.key}@{event.event_time}"
                        )
                else:
                    keep.append(event)
            self.right_buffer[key] = keep
        return (
            f"evicted {evicted_left} left and {evicted_right} "
            f"right past horizon {horizon}; unmatched exits "
            f"carry {len(self.unmatched_left)} and "
            f"{len(self.unmatched_right)}, named and countable"
        )

    def ledger(self) -> str:
        held = sum(
            len(events) for events in self.left_buffer.values()
        ) + sum(
            len(events) for events in self.right_buffer.values()
        )
        return (
            f"{len(self.matches)} match(es), "
            f"{len(self.unmatched_left)} unmatched left, "
            f"{len(self.unmatched_right)} unmatched right, "
            f"{held} event(s) still buffered; a join that only "
            "reports matches is hiding its losses"
        )

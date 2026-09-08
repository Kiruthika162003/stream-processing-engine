"""Operators: small machines that count everything passing through them.

A streaming topology is only debuggable if every operator can
answer two questions at any moment: how many events came in,
and where did they go. The map changes values and never
counts, one in, one out; the filter drops events and is
therefore required to name its reason, because a stream that
shrinks somewhere between source and sink is the single most
common mystery in this field and "the filter ate them" should
be a lookup, not an investigation. The rekey changes routing,
which is invisible in counts and decisive in behavior, so it
keeps a route census showing where the keys went. Chains
compose operators in order and report per-stage counts, the
pipeline's own X-ray, taken continuously and free to read.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.errors import Invalid
from rill.events import Event


@dataclass
class MapValues:
    name: str
    fn: Callable[[int], int]
    seen: int = 0

    def process(self, event: Event) -> list[Event]:
        self.seen += 1
        return [
            Event(
                key=event.key,
                value=self.fn(event.value),
                event_time=event.event_time,
                arrival=event.arrival,
            )
        ]

    def census(self) -> str:
        return f"{self.name}: {self.seen} in, {self.seen} out"


@dataclass
class FilterEvents:
    name: str
    keep: Callable[[Event], bool]
    reason: str
    seen: int = 0
    dropped: int = 0

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise Invalid(
                f"{self.name}: a filter that cannot say why it "
                "drops turns a lookup into an investigation"
            )

    def process(self, event: Event) -> list[Event]:
        self.seen += 1
        if self.keep(event):
            return [event]
        self.dropped += 1
        return []

    def census(self) -> str:
        return (
            f"{self.name}: {self.seen} in, "
            f"{self.seen - self.dropped} out, {self.dropped} "
            f"dropped ({self.reason})"
        )


@dataclass
class Rekey:
    name: str
    route: Callable[[Event], str]
    routes: dict[str, int] = field(default_factory=dict)

    def process(self, event: Event) -> list[Event]:
        new_key = self.route(event)
        if not new_key:
            raise Invalid(
                f"{self.name}: routed {event.key} to an empty "
                "key; events without keys route nowhere"
            )
        self.routes[new_key] = self.routes.get(new_key, 0) + 1
        return [
            Event(
                key=new_key,
                value=event.value,
                event_time=event.event_time,
                arrival=event.arrival,
            )
        ]

    def census(self) -> str:
        spread = ", ".join(
            f"{key}:{count}"
            for key, count in sorted(self.routes.items())
        )
        return (
            f"{self.name}: rerouted to {len(self.routes)} "
            f"key(s) ({spread}); invisible in counts, decisive "
            "in behavior"
        )


@dataclass
class Chain:
    stages: list

    def __post_init__(self) -> None:
        if not self.stages:
            raise Invalid("an empty chain processes nothing")

    def process(self, event: Event) -> list[Event]:
        current = [event]
        for stage in self.stages:
            emitted = []
            for held in current:
                emitted.extend(stage.process(held))
            current = emitted
            if not current:
                break
        return current

    def xray(self) -> str:
        lines = ["the pipeline's own X-ray:"]
        lines.extend(
            f"  {stage.census()}" for stage in self.stages
        )
        return "\n".join(lines)

"""Many sources, one watermark, and the quiet partition that freezes time.

A pipeline reading four partitions advances its watermark to
the minimum of the four, because a promise about the past
must hold for every source that can still speak. The trap
inside that correct rule is the quiet partition: one source
with no traffic keeps its watermark at wherever it last
stood, the minimum stops moving, and every window in the
pipeline waits on a partition that has nothing to say. The
idleness timeout is the escape hatch: a source silent past
the timeout is marked idle and excused from the minimum until
it speaks again, at which point it rejoins, and its first
events are checked against the advanced watermark since time
moved on without it. The census names the source holding the
watermark back at any moment, because "the watermark is
stuck" is a mystery and "partition 3 has said nothing for an
hour" is a ticket.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SourceClock:
    name: str
    watermark: int = -1
    last_spoke: int = -1
    idle: bool = False


@dataclass
class MultiSourceWatermark:
    idle_timeout: int
    sources: dict[str, SourceClock] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.idle_timeout <= 0:
            raise Invalid("the idleness timeout must be positive")

    def add_source(self, name: str) -> None:
        if name in self.sources:
            raise Invalid(f"{name} already registered")
        self.sources[name] = SourceClock(name=name)

    def speak(self, name: str, event_time: int, now: int) -> str:
        clock = self.sources.get(name)
        if clock is None:
            raise Invalid(f"{name} is not a registered source")
        rejoined = clock.idle
        others_speaking = [
            other.watermark
            for other in self.sources.values()
            if not other.idle and other.name != name
        ]
        clock.idle = False
        clock.last_spoke = now
        clock.watermark = max(clock.watermark, event_time)
        if rejoined:
            baseline = (
                min(others_speaking)
                if others_speaking
                else event_time
            )
            behind = baseline - event_time
            note = (
                f"; time moved on without it, and this event "
                f"is {behind} tick(s) behind the combined "
                "watermark"
                if behind > 0
                else "; it caught up cleanly"
            )
            return f"{name} rejoins the minimum{note}"
        return f"{name} at {clock.watermark}"

    def mark_idle(self, now: int) -> list[str]:
        marked = []
        for clock in self.sources.values():
            if (
                not clock.idle
                and clock.last_spoke >= 0
                and now - clock.last_spoke > self.idle_timeout
            ):
                clock.idle = True
                marked.append(
                    f"{clock.name} silent for "
                    f"{now - clock.last_spoke}, excused from "
                    "the minimum"
                )
        return marked

    def combined(self) -> int:
        speaking = [
            clock.watermark
            for clock in self.sources.values()
            if not clock.idle
        ]
        if not speaking:
            raise Invalid(
                "every source is idle; the pipeline has no "
                "opinion about time"
            )
        return min(speaking)

    def holdback_census(self) -> str:
        speaking = [
            clock
            for clock in self.sources.values()
            if not clock.idle
        ]
        if not speaking:
            raise Invalid("nobody is speaking")
        slowest = min(speaking, key=lambda clock: clock.watermark)
        others = [
            clock.watermark
            for clock in speaking
            if clock.name != slowest.name
        ]
        if not others or slowest.watermark >= min(others):
            return "no single source holds the watermark back"
        gap = min(others) - slowest.watermark
        return (
            f"{slowest.name} holds the watermark back by "
            f"{gap} tick(s); a stuck watermark is a mystery, "
            "this is a ticket"
        )

"""Backpressure in a topology: the slow stage sets everyone's speed, honestly.

Between two operators sits a bounded channel, and the bound is
the design: when the downstream stage slows, its input channel
fills, the upstream stage blocks on the full channel, its own
input fills in turn, and the slowness propagates hop by hop
back to the source, which is exactly what should happen,
because the alternative, unbounded channels, converts a slow
sink into an out-of-memory three stages away at three in the
morning. The propagation drill runs a three-stage line with a
suddenly slow sink and reports the fill order of the channels,
upstream-ward, with the tick each one filled, so the timeline
reads like the incident will: sink slowed, channel two filled,
channel one filled, source paused, and every stage's stall is
attributed to the stage below it, not to the stage itself,
because blaming the paused source for pausing is how the
wrong team gets paged.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Channel:
    name: str
    capacity: int
    held: int = 0
    filled_at: int | None = None

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise Invalid("a channel needs capacity")

    def offer(self, now: int) -> bool:
        if self.held >= self.capacity:
            if self.filled_at is None:
                self.filled_at = now
            return False
        self.held += 1
        return True

    def take(self) -> bool:
        if self.held == 0:
            return False
        self.held -= 1
        if self.held < self.capacity:
            self.filled_at = None
        return True


@dataclass
class ThreeStageLine:
    channel_one: Channel = field(
        default_factory=lambda: Channel("channel-1", 3)
    )
    channel_two: Channel = field(
        default_factory=lambda: Channel("channel-2", 3)
    )
    sink_rate: int = 1
    source_paused_at: int | None = None
    timeline: list[str] = field(default_factory=list)

    def slow_the_sink(self, now: int) -> None:
        self.sink_rate = 0
        self.timeline.append(f"[{now}] sink slowed")

    def tick(self, now: int) -> None:
        for _ in range(self.sink_rate):
            self.channel_two.take()
        if self.channel_two.offer(now):
            self.channel_one.take()
        elif self.channel_two.filled_at == now:
            self.timeline.append(
                f"[{now}] channel-2 filled; stage two stalls, "
                "attributed to the sink below it"
            )
        if not self.channel_one.offer(now):
            if self.channel_one.filled_at == now:
                self.timeline.append(
                    f"[{now}] channel-1 filled; stage one "
                    "stalls, attributed to stage two"
                )
            if self.source_paused_at is None:
                self.source_paused_at = now
                self.timeline.append(
                    f"[{now}] source paused; the slowness "
                    "reached the front door, which is the "
                    "design working"
                )

    def incident_readout(self) -> str:
        if not self.timeline:
            raise Invalid("nothing happened yet")
        lines = ["the timeline reads like the incident will:"]
        lines.extend(f"  {entry}" for entry in self.timeline)
        lines.append(
            "every stall is attributed to the stage below it, "
            "because blaming the paused source is how the "
            "wrong team gets paged"
        )
        return "\n".join(lines)

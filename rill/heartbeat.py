"""Source heartbeats: the difference between quiet and dead, decided early.

A source that sends nothing is either healthy with nothing to
say or gone, and everything downstream needs the distinction
long before a human would notice: the idle marker needs it to
excuse the right sources, the lag alarm needs it to skip
sources that owe nothing, and the oncall needs it phrased as
a fact. Heartbeats settle it: a healthy source with no events
sends a pulse on schedule, so silence splits into two
readable states, pulsing-but-eventless, which is quiet, and
pulseless, which after a grace period is dead, with the last
pulse timestamped in the verdict. The grace period is
deliberately two pulses wide, because networks drop one pulse
routinely and a detector that declares death on a single
missed heartbeat pages someone weekly about sources in
perfect health.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

GRACE_PULSES = 2


@dataclass
class HeartbeatMonitor:
    pulse_interval: int
    last_pulse: dict[str, int] = field(default_factory=dict)
    last_event: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.pulse_interval < 1:
            raise Invalid("the pulse needs an interval")

    def pulse(self, source: str, now: int) -> None:
        if not source:
            raise Invalid("pulses carry their source")
        self.last_pulse[source] = now

    def event(self, source: str, now: int) -> None:
        self.last_pulse[source] = now
        self.last_event[source] = now

    def read(self, source: str, now: int) -> str:
        pulse_at = self.last_pulse.get(source)
        if pulse_at is None:
            return f"{source}: never heard from; not yet a fact"
        silence = now - pulse_at
        deadline = self.pulse_interval * GRACE_PULSES
        if silence > deadline:
            return (
                f"{source}: DEAD, last pulse at {pulse_at}, "
                f"{silence} tick(s) of silence against a "
                f"grace of {deadline}; phrased as a fact for "
                "the oncall"
            )
        event_at = self.last_event.get(source)
        if event_at is None or event_at < pulse_at:
            return (
                f"{source}: quiet, pulsing but eventless; "
                "healthy with nothing to say"
            )
        return f"{source}: active, last event at {event_at}"

    def roll(self, now: int) -> str:
        if not self.last_pulse:
            raise Invalid("no sources to roll-call")
        dead = [
            source
            for source in sorted(self.last_pulse)
            if "DEAD" in self.read(source, now)
        ]
        if not dead:
            return (
                f"{len(self.last_pulse)} source(s), all "
                "accounted for, quiet or loud"
            )
        return (
            f"{len(dead)} dead of {len(self.last_pulse)}: "
            + ", ".join(dead)
        )

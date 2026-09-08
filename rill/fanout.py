"""Fan-out: one stream, many sinks, each reading at its own pace.

A stream feeding three sinks is three subscriptions, not one
delivery, and the design decision hiding in that sentence is
independence: each sink tracks its own position, so the slow
warehouse loader does not hold back the fast alerting sink,
and the price of independence is retention, since the log
must keep everything the slowest subscriber still needs. The
spread report is the operational read: positions per sink,
the spread between fastest and slowest, and the retention
hostage line naming who anchors the tail, because when disk
fills the conversation is "the warehouse loader is 40,000
events behind and pinning 2 hours of log", which has an
owner, while "the topic is big" has none. Detaching a sink
is explicit and logged, the alternative being the subscriber
that everyone forgot, anchoring retention forever from an
office nobody works in anymore.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class FanOut:
    head: int = 0
    positions: dict[str, int] = field(default_factory=dict)
    detached: list[str] = field(default_factory=list)

    def subscribe(self, sink: str) -> str:
        if not sink:
            raise Invalid("subscriptions carry a name")
        if sink in self.positions:
            raise Invalid(f"{sink} is already subscribed")
        self.positions[sink] = self.head
        return f"{sink} subscribed at {self.head}"

    def publish(self, count: int = 1) -> None:
        if count < 1:
            raise Invalid("publishing nothing moves nothing")
        self.head += count

    def advance(self, sink: str, to_position: int) -> str:
        held = self.positions.get(sink)
        if held is None:
            raise Invalid(f"{sink} is not subscribed")
        if to_position < held:
            raise Invalid(f"{sink} cannot read backwards")
        if to_position > self.head:
            raise Invalid(f"{sink} cannot read the future")
        self.positions[sink] = to_position
        return f"{sink} at {to_position} of {self.head}"

    def detach(self, sink: str, reason: str) -> str:
        if sink not in self.positions:
            raise Invalid(f"{sink} is not subscribed")
        if not reason.strip():
            raise Invalid(
                "detaching without a reason creates the "
                "subscriber everyone forgot"
            )
        del self.positions[sink]
        self.detached.append(f"{sink}: {reason}")
        return f"{sink} detached: {reason}"

    def spread_report(self) -> str:
        if not self.positions:
            raise Invalid("no subscribers, no spread")
        slowest = min(
            self.positions, key=lambda s: self.positions[s]
        )
        fastest = max(
            self.positions, key=lambda s: self.positions[s]
        )
        spread = (
            self.positions[fastest] - self.positions[slowest]
        )
        pinned = self.head - self.positions[slowest]
        return (
            f"{len(self.positions)} sink(s), spread {spread}; "
            f"{slowest} is {pinned} event(s) behind the head "
            "and anchors the tail, which has an owner, while "
            "the-topic-is-big has none"
        )

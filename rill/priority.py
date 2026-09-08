"""Priority lanes: one stream, two speeds, and starvation made impossible.

Some events in a stream are more urgent than the stream: the
fraud check outranks the analytics ping even when both arrive
in the same partition, so the consumer splits its intake into
lanes and drains the express lane first. The starvation guard
is the design's conscience: strict priority starves the slow
lane whenever the express lane stays busy, so the drain ratio
is a contract, N express to one standard, guaranteed even
under express flood, and the meter proves the contract with
counts rather than intentions. The lane assignment is refused
without a rule, since an event's urgency is a property the
producer declares, not something the consumer guesses from
size or smell, and guessed urgency is how the analytics ping
that happened to be small ended up outrunning the fraud
check that happened to be large.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class PriorityLanes:
    express_per_standard: int
    express: list[str] = field(default_factory=list)
    standard: list[str] = field(default_factory=list)
    drained_express: int = 0
    drained_standard: int = 0
    express_since_standard: int = 0

    def __post_init__(self) -> None:
        if self.express_per_standard < 1:
            raise Invalid("the ratio must be at least one")

    def enqueue(self, event_id: str, lane: str) -> None:
        if lane == "express":
            self.express.append(event_id)
        elif lane == "standard":
            self.standard.append(event_id)
        else:
            raise Invalid(
                f"{lane} is not a lane; urgency is declared "
                "by the producer, not guessed from size or "
                "smell"
            )

    def drain_one(self) -> str | None:
        express_due = (
            self.express
            and (
                not self.standard
                or self.express_since_standard
                < self.express_per_standard
            )
        )
        if express_due:
            event_id = self.express.pop(0)
            self.drained_express += 1
            self.express_since_standard += 1
            return f"express: {event_id}"
        if self.standard:
            event_id = self.standard.pop(0)
            self.drained_standard += 1
            self.express_since_standard = 0
            return f"standard: {event_id}"
        if self.express:
            event_id = self.express.pop(0)
            self.drained_express += 1
            return f"express: {event_id}"
        return None

    def contract_meter(self) -> str:
        if self.drained_standard == 0:
            if self.drained_express == 0:
                raise Invalid("nothing drained")
            return (
                f"{self.drained_express} express drained, "
                "standard untouched so far; watch this number"
            )
        ratio = self.drained_express / self.drained_standard
        return (
            f"{self.drained_express} express to "
            f"{self.drained_standard} standard "
            f"({ratio:.1f}:1 against a contract of "
            f"{self.express_per_standard}:1); proven with "
            "counts rather than intentions"
        )

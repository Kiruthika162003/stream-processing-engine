"""The cold start: where a new consumer begins is a business decision.

A consumer joining an existing stream faces three doors:
earliest replays the whole retained history and arrives with
complete state and a huge bill; latest starts now, cheap and
instantly current, with state that pretends the past never
happened; and snapshot bootstraps from a prepared state at a
known position, then tails, paying a medium bill for complete
state without the full replay. The chooser refuses to
default, because each door is wrong for someone: earliest for
the alerting consumer that would re-fire a week of alerts,
latest for the billing consumer that would invoice from
amnesia, and the decision record it emits names the door, the
bill, and the state completeness, so the choice survives its
chooser and the next oncall does not re-litigate it from the
name of the config flag alone.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

DOORS = ("earliest", "latest", "snapshot")


@dataclass(frozen=True)
class ColdStart:
    retained_events: int
    snapshot_position: int
    head_position: int

    def __post_init__(self) -> None:
        if self.head_position < self.snapshot_position:
            raise Invalid("the snapshot cannot be ahead of the head")
        if self.retained_events < 0:
            raise Invalid("retention cannot be negative")

    def price(self, door: str) -> tuple[int, str]:
        if door == "earliest":
            return self.retained_events, (
                "complete state, and a consumer that re-acts "
                "to history re-fires a week of alerts"
            )
        if door == "latest":
            return 0, (
                "instantly current, with state that pretends "
                "the past never happened; billing from "
                "amnesia"
            )
        if door == "snapshot":
            tail = self.head_position - self.snapshot_position
            return tail, (
                "complete state from the snapshot, tail only; "
                "the medium bill"
            )
        raise Invalid(f"{door} is not a door; the three are {DOORS}")

    def decision_record(
        self, door: str, consumer: str, reason: str
    ) -> str:
        if not reason.strip():
            raise Invalid(
                "a cold-start choice without its reason gets "
                "re-litigated from the config flag's name "
                "alone"
            )
        bill, nature = self.price(door)
        return (
            f"{consumer} starts at {door}: {bill} event(s) to "
            f"process, {nature}; reason: {reason}"
        )

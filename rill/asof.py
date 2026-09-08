"""As-of joins: enrich an event with the reference value that was current then.

A trade at 10:03 must be priced with the exchange rate that
was in effect at 10:03, not the rate now, and a naive join
that grabs the latest rate silently reprices history every
time the rate ticks. The as-of join keeps the reference
stream as a timeline of versioned values and, for each event,
finds the reference version whose validity covers the event's
time, which is the last version at or before it. The edge that
bites is the event that precedes every reference version, a
trade before the first rate was published, and the join
refuses to guess it forward from a rate that did not exist
yet, returning a named no-reference rather than the earliest
rate pretending to have applied. The temporal correctness is
the entire point: an as-of join that used the current value
would pass every test with static data and corrupt every
backfill, which is the bug that ships because the tests never
moved the clock.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class AsOfJoin:
    reference: list[tuple[int, int]] = field(
        default_factory=list
    )

    def publish(self, valid_from: int, value: int) -> None:
        if self.reference and valid_from <= self.reference[-1][0]:
            raise Invalid(
                "reference versions publish in time order"
            )
        self.reference.append((valid_from, value))

    def value_at(self, event_time: int) -> str:
        applicable = [
            (valid_from, value)
            for valid_from, value in self.reference
            if valid_from <= event_time
        ]
        if not applicable:
            return (
                f"no reference at {event_time}: the event "
                "precedes every version, and guessing forward "
                "from a value that did not exist yet is the "
                "backfill corruption"
            )
        valid_from, value = applicable[-1]
        return (
            f"at {event_time}: value {value} (in effect since "
            f"{valid_from}); the version current then, not now"
        )

    def enrich(self, event_time: int) -> int | None:
        applicable = [
            value
            for valid_from, value in self.reference
            if valid_from <= event_time
        ]
        return applicable[-1] if applicable else None

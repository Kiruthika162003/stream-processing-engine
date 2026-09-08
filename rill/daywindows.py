"""Calendar windows: the day that was 23 hours long, handled on purpose.

Daily aggregates sound like tumbling windows of 24 hours
until the clocks change: the spring-forward day is 23 hours,
the fall-back day is 25, and a pipeline windowing by fixed
86,400-tick spans drifts an hour off the calendar twice a
year, quietly splitting one business day's revenue across two
rows. The calendar windower assigns events by the day's
declared span, taking a table of irregular days, and its
report names the irregulars it honored, because the auditor
who finds a 23-hour revenue day needs the sentence "spring
forward, this day was short on purpose" attached to the row,
not discovered in a wiki. The refusal is for the silent
alternative: a day table with a gap or an overlap is rejected
at load, since a missing hour between days is where events
vanish without even the courtesy of being late.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

STANDARD_DAY = 24


@dataclass
class CalendarDays:
    day_starts: list[tuple[str, int]]

    def __post_init__(self) -> None:
        if len(self.day_starts) < 2:
            raise Invalid("a calendar needs at least two days")
        for (_, start), (_, next_start) in zip(
            self.day_starts, self.day_starts[1:], strict=False
        ):
            if next_start <= start:
                raise Invalid(
                    "days run forward; a gap or an overlap is "
                    "where events vanish without even the "
                    "courtesy of being late"
                )

    def assign(self, event_time: int) -> str:
        for (label, start), (_, next_start) in zip(
            self.day_starts, self.day_starts[1:], strict=False
        ):
            if start <= event_time < next_start:
                return label
        raise Invalid(
            f"{event_time} falls outside the loaded calendar"
        )

    def irregular_report(self) -> str:
        notes = []
        for (label, start), (_, next_start) in zip(
            self.day_starts, self.day_starts[1:], strict=False
        ):
            span = next_start - start
            if span == STANDARD_DAY:
                continue
            kind = (
                "spring forward, short on purpose"
                if span < STANDARD_DAY
                else "fall back, long on purpose"
            )
            notes.append(
                f"{label}: {span} hour(s), {kind}"
            )
        if not notes:
            return "every day ran its standard 24"
        lines = [
            f"{len(notes)} irregular day(s), each with its "
            "sentence attached to the row:"
        ]
        lines.extend(f"  {note}" for note in notes)
        return "\n".join(lines)

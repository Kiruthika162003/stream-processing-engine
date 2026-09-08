"""Virtual time: the test clock that makes a week cost a millisecond.

Testing a streaming pipeline against the wall clock is a
choice between slow tests and flaky ones, usually both; the
virtual clock replaces waiting with declaring: time advances
because the test says so, timers fire deterministically at
their declared instants, and a week of session expiries runs
in the time it takes to add integers. The harness holds the
clock and a schedule of callbacks, advancing executes every
callback due in order with the clock set to each one's
instant, because a callback that reads the clock mid-fire
must see its own scheduled time, not the destination, or
cascading timers drift. The discipline the harness enforces
is the one flaky tests violate: nothing in the system under
test may touch the wall clock, and the harness's own audit
counts how many times it was asked, with the only acceptable
answer being zero.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class VirtualClock:
    now: int = 0
    schedule: list[tuple[int, str, Callable[[], None]]] = field(
        default_factory=list
    )
    fired: list[str] = field(default_factory=list)
    wall_clock_asks: int = 0

    def call_at(
        self, instant: int, label: str, callback: Callable[[], None]
    ) -> None:
        if instant < self.now:
            raise Invalid(
                f"{label} scheduled at {instant}, already "
                f"past {self.now}; the past is not a venue"
            )
        self.schedule.append((instant, label, callback))

    def advance_to(self, destination: int) -> list[str]:
        if destination < self.now:
            raise Invalid("virtual time also refuses to rewind")
        fired_now = []
        while True:
            due = sorted(
                (entry for entry in self.schedule
                 if entry[0] <= destination),
                key=lambda entry: (entry[0], entry[1]),
            )
            if not due:
                break
            instant, label, callback = due[0]
            self.schedule.remove(due[0])
            self.now = instant
            callback()
            self.fired.append(f"{label}@{instant}")
            fired_now.append(f"{label}@{instant}")
        self.now = destination
        return fired_now

    def wall_clock(self) -> None:
        self.wall_clock_asks += 1
        raise Invalid(
            "the system under test touched the wall clock; "
            "this is where flaky tests come from"
        )

    def audit(self) -> str:
        return (
            f"{len(self.fired)} callback(s) fired, "
            f"{self.wall_clock_asks} wall-clock ask(s); the "
            "only acceptable second number is zero"
        )

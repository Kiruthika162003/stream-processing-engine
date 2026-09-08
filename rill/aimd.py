"""AIMD concurrency: probe the limit up one at a time, cut it in half on overload.

A fixed in-flight limit is wrong in both directions: set it low
and the pipeline leaves throughput on the table, set it high and
a slow dependency lets requests pile up until the whole stage
collapses under its own queue. AIMD, the rule that keeps TCP from
melting the internet, adapts the limit instead of guessing it.
Every success nudges the limit up by one, additive increase, a
cautious probe for more room, and every overload signal, a
timeout or a rejection, halves it, multiplicative decrease, a
fast retreat from the cliff. The asymmetry is deliberate and it
draws the familiar sawtooth: the limit climbs slowly while things
are fine and drops hard the instant they are not, because
overshooting the safe concurrency is far more expensive than
undershooting it. This module holds the current limit between a
floor and a ceiling, increases on success and halves on
overload, and never leaves the bounds, so the sawtooth and its
deliberately lopsided slopes are a measurement rather than a
diagram.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class AimdLimiter:
    limit: int
    floor: int
    ceiling: int

    def __post_init__(self) -> None:
        if not self.floor <= self.limit <= self.ceiling:
            raise Invalid("need floor <= limit <= ceiling")
        if self.floor < 1:
            raise Invalid("floor must be at least one")

    def on_success(self) -> int:
        self.limit = min(self.ceiling, self.limit + 1)
        return self.limit

    def on_overload(self) -> int:
        self.limit = max(self.floor, self.limit // 2)
        return self.limit

    def overloads_to_floor(self) -> int:
        count = 0
        value = self.limit
        while value > self.floor:
            value = max(self.floor, value // 2)
            count += 1
        return count

    def successes_to_ceiling(self) -> int:
        return self.ceiling - self.limit

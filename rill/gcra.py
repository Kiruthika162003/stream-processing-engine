"""GCRA: metering a rate with one timestamp, the theoretical arrival time.

The token bucket and leaky bucket meter a rate by maintaining a
counter that refills or drains over time; the generic cell rate
algorithm meters the same rate with a single timestamp and no
counter at all. It tracks a theoretical arrival time, the earliest
instant the next conforming request should come if the source were
running exactly at the limit, and admits a request when it arrives
no earlier than that time minus a burst tolerance. On admitting
one, the theoretical arrival time advances by the emission
interval, one over the rate, from whichever is later of the
current time or the old theoretical time, so a source that pauses
does not bank unlimited credit but a source that has been quiet
can fire a burst up to the tolerance before the theoretical time
catches up to real time. The whole limiter state is that one
timestamp, updated with a compare and an add per request, which is
why GCRA is what hardware and high-throughput API gateways
actually use where a per-key counter would be too much state. It
is mathematically equivalent to a leaky bucket of depth equal to
the tolerance, expressed as a time rather than a level. This module
runs the meter, admitting or rejecting by the theoretical arrival
time, so the burst-then-settle behavior is a measured sequence
against the emission interval.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class Gcra:
    interval: int
    tolerance: int
    _tat: int = 0
    _started: bool = False

    def __post_init__(self) -> None:
        if self.interval <= 0 or self.tolerance < 0:
            raise Invalid("interval must be positive and tolerance non-negative")

    def allow(self, now: int) -> bool:
        if not self._started:
            self._tat = now
            self._started = True
        if now < self._tat - self.tolerance:
            return False
        self._tat = max(now, self._tat) + self.interval
        return True

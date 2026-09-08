"""Retry backoff: exponential without jitter keeps a failed cohort in lockstep.

Exponential backoff doubles the wait after each failed retry and
caps it, which spaces one client's retries out nicely and does
nothing for a crowd. A thousand clients that all failed on the
same outage all compute the same doubling delays and all retry at
the same instants, so the server that just came back gets hit by
the whole synchronized cohort, fails again, and the cohort
marches in step through the next delay: a thundering herd that
backoff alone never breaks up because every member follows the
identical schedule. Jitter is what decorrelates them. Full jitter
picks the actual wait uniformly between zero and the capped delay,
so two clients on the same attempt land at different times and the
herd smears out across the window instead of arriving as a spike.
The trade is a shorter average wait under full jitter, roughly
half the cap, against the lockstep it dissolves. This module
computes the capped exponential delay and applies jitter from an
injected roll, so the schedule is exact and the tests are not at
the mercy of a hidden random seed.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class Backoff:
    base: int
    factor: int
    cap: int

    def __post_init__(self) -> None:
        if self.base <= 0 or self.cap <= 0:
            raise Invalid("base and cap must be positive")
        if self.factor < 1:
            raise Invalid("factor must be at least one")

    def delay(self, attempt: int) -> int:
        if attempt < 0:
            raise Invalid("attempt cannot be negative")
        return min(self.cap, self.base * self.factor**attempt)

    def full_jitter(self, attempt: int, roll: float) -> int:
        if not 0.0 <= roll < 1.0:
            raise Invalid("roll is a fraction in [0, 1)")
        return int(roll * self.delay(attempt))

    def equal_jitter(self, attempt: int, roll: float) -> int:
        if not 0.0 <= roll < 1.0:
            raise Invalid("roll is a fraction in [0, 1)")
        half = self.delay(attempt) // 2
        return half + int(roll * half)


def cohort_spread(delays: list[int]) -> int:
    if not delays:
        raise Invalid("no delays to measure")
    return max(delays) - min(delays)

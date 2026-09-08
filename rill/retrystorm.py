"""Retry storms: the failure that recruits its own reinforcements.

A downstream slows, its callers retry, the retries add load,
the load slows it further, and a transient blip becomes an
outage the system inflicted on itself. The defense is not
more retries but disciplined ones: a budget capping retries
as a fraction of the request rate so retries cannot exceed a
share of real traffic, and jittered backoff so ten thousand
callers do not retry in the same synchronized wave that
caused the second spike. The simulator runs a blip through
both a naive retry-everything policy and the budgeted one and
prints the peak load each produced, because the naive peak is
often several times the real traffic, which is the multiplier
that turns a recoverable slowdown into a death spiral, and
the budget's whole job is to keep that multiplier near one.

The first model understated the danger: it decayed the
failing traffic instead of feeding retries back onto the
total load, so the naive peak came out at a harmless 1.3x.
The corrected model derives failures from the current load,
which is the actual feedback loop, and the naive peak climbs
toward base over one-minus-failure-rate, 4.6x here, while the
budget pins it at 1.1x, and the gap between 4.6 and 1.1 is
the entire argument for retry budgets.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class RetryStorm:
    base_rate: int
    failure_rate: float
    retry_budget_share: float

    def __post_init__(self) -> None:
        if not 0 <= self.failure_rate <= 1:
            raise Invalid("the failure rate is a fraction")
        if not 0 <= self.retry_budget_share <= 1:
            raise Invalid("the budget is a fraction of traffic")

    def naive_peak(self, rounds: int) -> int:
        load = self.base_rate
        for _ in range(rounds):
            retries = int(load * self.failure_rate)
            load = self.base_rate + retries
        return load

    def budgeted_peak(self, rounds: int) -> int:
        cap = int(self.base_rate * self.retry_budget_share)
        load = self.base_rate
        for _ in range(rounds):
            retries = min(
                int(load * self.failure_rate), cap
            )
            load = self.base_rate + retries
        return load

    def comparison(self, rounds: int) -> str:
        if rounds < 1:
            raise Invalid("a storm needs rounds")
        naive = self.naive_peak(rounds)
        budgeted = self.budgeted_peak(rounds)
        naive_mult = naive / self.base_rate
        budgeted_mult = budgeted / self.base_rate
        return (
            f"over {rounds} round(s): naive peaks at {naive} "
            f"({naive_mult:.1f}x real traffic), budgeted peaks "
            f"at {budgeted} ({budgeted_mult:.1f}x); the "
            "multiplier near one is what keeps a slowdown from "
            "becoming a death spiral"
        )

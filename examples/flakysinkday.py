"""A flaky-sink day: a breaker trips, a cohort scatters, a tail is hedged, a saga unwinds.

Run with: python -m examples.flakysinkday
"""

from __future__ import annotations

from rill.backoff import Backoff, cohort_spread
from rill.bulkhead import Bulkhead
from rill.circuitbreaker import CircuitBreaker
from rill.hedged import Hedger
from rill.saga import Saga


def morning_the_breaker():
    breaker = CircuitBreaker(threshold=2, cooldown=10)
    breaker.on_failure(now=0)
    breaker.on_failure(now=1)
    opened = breaker.state(now=1)
    recovered = breaker.state(now=11)
    print(f"breaker:  {opened} at the trip, {recovered} after the cooldown")


def midday_the_cohort():
    backoff = Backoff(base=1, factor=2, cap=1000)
    lockstep = cohort_spread([backoff.delay(6) for _ in range(20)])
    scattered = cohort_spread(
        [backoff.full_jitter(6, number / 20) for number in range(20)]
    )
    print(f"backoff:  spread {lockstep} in lockstep, {scattered} with jitter")


def afternoon_the_tail():
    primaries = [10] * 95 + [500] * 5
    plain = Hedger(hedge_delay=10**9, backup_latency=20).batch(primaries)
    hedged = Hedger(hedge_delay=50, backup_latency=20).batch(primaries)
    print(f"hedged:   p99 {plain['p99']} plain, {hedged['p99']} hedged")


def dusk_the_bulkhead():
    bulk = Bulkhead(per_partition=2)
    bulk.acquire("greedy")
    bulk.acquire("greedy")
    bulk.acquire("greedy")
    victim_served = bulk.acquire("victim")
    print(f"bulkhead: victim still served: {victim_served}")


def night_the_saga():
    saga = Saga(steps=("charge", "ship", "notify"))
    run = saga.execute((True, True, False))
    print(f"saga:     compensated {list(run.compensated)}")


def main() -> int:
    morning_the_breaker()
    midday_the_cohort()
    afternoon_the_tail()
    dusk_the_bulkhead()
    night_the_saga()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

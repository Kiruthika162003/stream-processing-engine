"""Fraud night: the join, the timer, the replay, and the express lane.

Run with: python -m examples.fraudnight
"""

from __future__ import annotations

from rill.dedupe import Deduper
from rill.events import Event
from rill.joins import IntervalJoin
from rill.priority import PriorityLanes
from rill.timers import TimerService


def at(key: str, event_time: int) -> Event:
    return Event(
        key=key, value=1, event_time=event_time,
        arrival=event_time,
    )


def the_join_that_smells_fraud():
    join = IntervalJoin(tolerance=3)
    join.feed_left(at("card-9", 100))
    join.feed_left(at("card-9", 102))
    notes = join.feed_right(at("card-9", 101))
    print(f"join:    {len(notes)} charges within tolerance of one auth")
    print(f"         {join.ledger().splitlines()[0]}")


def the_timer_on_the_silent_case():
    timers = TimerService()
    timers.set_timer("case-441", deadline=130)
    timers.set_timer("case-442", deadline=110)
    timers.clear("case-441")
    fired = timers.advance(watermark=140)
    print(f"timer:   {fired[0]}")
    print(f"         {timers.storm_report()}")


def the_replayed_alert():
    deduper = Deduper(horizon=1000)
    sent = [
        alert_id
        for alert_id in ("alert-1", "alert-2", "alert-1")
        if deduper.offer(alert_id, now=100)
    ]
    print(f"dedupe:  {len(sent)} alert(s) sent, replay refused")


def the_express_lane():
    lanes = PriorityLanes(express_per_standard=2)
    for number in range(4):
        lanes.enqueue(f"fraud-check-{number}", "express")
        lanes.enqueue(f"metrics-{number}", "standard")
    order = [lanes.drain_one() for _ in range(6)]
    print(f"lanes:   first three drained: {order[:3]}")
    print(f"         {lanes.contract_meter().split(';')[0]}")


def main() -> int:
    the_join_that_smells_fraud()
    the_timer_on_the_silent_case()
    the_replayed_alert()
    the_express_lane()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

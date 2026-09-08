"""A lag day: the queue grows, the tail approaches, the poison surfaces.

Run with: python -m examples.lagday
"""

from __future__ import annotations

from rill.backpressure import ThreeStageLine
from rill.lag import LagTracker
from rill.poison import PoisonPolicy
from rill.retention import RetentionMargin


def nine_am_the_lag():
    tracker = LagTracker(lag=0)
    for _ in range(4):
        tracker.observe_window(arrived=120, drained=80)
    print(f"09:00  {tracker.verdict()}")
    print(f"       {tracker.batch_job_check()}")


def ten_am_the_cause():
    line = ThreeStageLine()
    for now in range(3):
        line.tick(now)
    line.slow_the_sink(3)
    for now in range(4, 12):
        line.tick(now)
    readout = line.incident_readout()
    for entry in readout.splitlines()[1:4]:
        print(f"10:00 {entry}")


def eleven_am_the_poison():
    policy = PoisonPolicy(retry_budget=2)
    for _ in range(3):
        policy.record_failure("p2:8841", "unparseable payload")
    print(f"11:00  {policy.dlq_page().splitlines()[0]}")
    print(f"       {policy.deploy_check()}")


def noon_the_tail():
    margin = RetentionMargin(retention_span=100)
    print(f"12:00  {margin.report_lag('billing-consumer', 92)}")
    margin.report_lag("billing-consumer", 104)
    print(f"       {margin.board().splitlines()[-1]}")


def one_pm_the_recovery():
    tracker = LagTracker(lag=160)
    for _ in range(3):
        tracker.observe_window(arrived=80, drained=120)
    print(f"13:00  {tracker.verdict()}")


def main() -> int:
    nine_am_the_lag()
    ten_am_the_cause()
    eleven_am_the_poison()
    noon_the_tail()
    one_pm_the_recovery()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""An ops week: the stall, the split, the canary, the rollback.

Run with: python -m examples.opsweek
"""

from __future__ import annotations

import contextlib

from rill.canaryflow import CanaryRouter
from rill.errors import Halted
from rill.hotpartition import HotSplitter
from rill.jobmanager import JobManagerElection
from rill.rollback import DeployRollback
from rill.watermarkstall import StallDetector


def monday_the_stall():
    detector = StallDetector(stall_threshold=10)
    detector.observe(0, 100, events_in=50)
    detector.observe(30, 100, events_in=50)
    print(f"monday:    {detector.verdict().split(';')[0]}")


def tuesday_the_split():
    splitter = HotSplitter(
        order_sensitive={"account-balance"}, fanout=4
    )
    for index in range(400):
        splitter.accumulate("trending-topic", index, 1)
    total = splitter.recombine("trending-topic", "sum")
    print(f"tuesday:   {splitter.balance_report('trending-topic').split(';')[0]}")
    print(f"           recombined to {total}, order preserved by exclusion")


def wednesday_the_election():
    election = JobManagerElection()
    election.acquire("jm-a", now=0)
    election.assign("jm-a", 1, "p0")
    election.acquire("jm-b", now=31)
    election.assign("jm-b", 2, "p0")
    with contextlib.suppress(Halted):
        election.assign("jm-a", 1, "p1")
    print(f"wednesday: {election.incident_summary()}")


def thursday_the_canary():
    router = CanaryRouter(canary_percent=20)
    keys = [f"key-{n}" for n in range(200)]
    canary = [k for k in keys if router.routes_to_canary(k)]
    for key in canary:
        router.record_old(key, 7)
        router.record_new(key, 7)
    print(f"thursday:  {router.promotion_gate()}")


def friday_the_rollback():
    incident = DeployRollback(
        deploy_position=8400,
        detection_position=9100,
        savepoint_position=8300,
    )
    print(f"friday:    {incident.blast_statement().split(';')[0]}")


def main() -> int:
    monday_the_stall()
    tuesday_the_split()
    wednesday_the_election()
    thursday_the_canary()
    friday_the_rollback()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

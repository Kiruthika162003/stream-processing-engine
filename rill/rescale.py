"""Rescaling stateful stages: the keys must arrive where their memories live.

Scaling a stateless stage is arithmetic; scaling a stateful
one is a moving day, because every key's state lives on the
worker its hash chose, and changing the worker count changes
the answer for stranded memories everywhere. The drill
measures three schemes on the same five hundred keys, going
from four workers to five, and the middle one carries this
module's recorded correction: the prose first claimed that
key groups assigned by contiguous ranges would move roughly
the fraction of capacity that changed, and the measurement
says 49 percent, against modulo's 76 and far above the 20 the
claim promised, because range boundaries shift for nearly
every worker when the divisor changes. Reaching the honest
minimum takes stickiness: keep the old assignment and move
only the groups the new worker needs, measured at 21 percent,
and the three bills side by side are the argument, since the
range scheme survives on plausibility and plausibility dies
next to a measured comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.content_hash import stable_bucket
from rill.errors import Invalid

KEY_GROUPS = 128


def modulo_home(key: str, workers: int) -> int:
    if workers < 1:
        raise Invalid("a stage needs workers")
    return stable_bucket(key, workers)


def range_home(key: str, workers: int) -> int:
    if workers < 1:
        raise Invalid("a stage needs workers")
    group = stable_bucket(key, KEY_GROUPS)
    return group * workers // KEY_GROUPS


def sticky_assignment(workers: int) -> dict[int, int]:
    if workers < 1:
        raise Invalid("a stage needs workers")
    assignment = dict.fromkeys(range(KEY_GROUPS), 0)
    for new_worker in range(1, workers):
        quota = KEY_GROUPS // (new_worker + 1)
        for _ in range(quota):
            loads: dict[int, int] = {}
            for holder in assignment.values():
                loads[holder] = loads.get(holder, 0) + 1
            donor = max(
                loads, key=lambda worker: (loads[worker], -worker)
            )
            moving = max(
                group
                for group, holder in assignment.items()
                if holder == donor
            )
            assignment[moving] = new_worker
    return assignment


def sticky_home(key: str, workers: int) -> int:
    group = stable_bucket(key, KEY_GROUPS)
    return sticky_assignment(workers)[group]


@dataclass(frozen=True)
class RescaleBill:
    scheme: str
    moved: int
    total: int

    def line(self) -> str:
        share = 100 * self.moved // self.total
        return (
            f"{self.scheme}: {self.moved} of {self.total} "
            f"key(s) move ({share}%)"
        )


def measure_move(
    keys: list[str], before: int, after: int
) -> list[RescaleBill]:
    if not keys:
        raise Invalid("no keys, no moving day")
    schemes = (
        ("modulo", modulo_home),
        ("ranges", range_home),
        ("sticky-groups", sticky_home),
    )
    return [
        RescaleBill(
            scheme=name,
            moved=sum(
                1
                for key in keys
                if home(key, before) != home(key, after)
            ),
            total=len(keys),
        )
        for name, home in schemes
    ]


def moving_day_report(
    keys: list[str], before: int, after: int
) -> str:
    bills = measure_move(keys, before, after)
    capacity_change = 100 * abs(after - before) // before
    return "\n".join(
        [
            f"rescaling {before} -> {after} worker(s), a "
            f"{capacity_change}% capacity change:",
            *(f"  {bill.line()}" for bill in bills),
            "plausibility dies next to a measured comparison",
        ]
    )

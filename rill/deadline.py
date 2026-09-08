"""Deadline propagation: the request that dies inflight should stop the work.

A synchronous request that fans into a streaming pipeline
carries a deadline, and honoring it is a chain: if the caller
gave up 200 milliseconds in, every stage still processing
that request is burning capacity for an answer nobody will
read. Deadline propagation threads the caller's expiry
through the pipeline so each stage checks before it starts,
and the check is a subtraction, remaining budget minus this
stage's typical cost, refusing to start work that cannot
finish in time rather than starting it and timing out
downstream, because a stage that starts doomed work has
converted one dead request into two dead stages. The
budget-exceeded refusal is an answer with the shortfall
named, so the caller learns the deadline was unrealistic
rather than the system slow, which are different bugs filed
against different teams.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class DeadlineChain:
    total_budget: int
    spent: int = 0
    stages_run: list[str] = field(default_factory=list)
    abandoned: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.total_budget < 1:
            raise Invalid("a deadline needs a budget")

    def remaining(self) -> int:
        return self.total_budget - self.spent

    def attempt(self, stage: str, cost: int) -> str:
        if cost < 1:
            raise Invalid("every stage costs something")
        if cost > self.remaining():
            self.abandoned.append(stage)
            return (
                f"{stage} refused: needs {cost}, "
                f"{self.remaining()} left; starting doomed "
                "work turns one dead request into two dead "
                "stages"
            )
        self.spent += cost
        self.stages_run.append(stage)
        return (
            f"{stage} ran in {cost}, {self.remaining()} budget "
            "left"
        )

    def verdict(self) -> str:
        if self.abandoned:
            return (
                f"deadline missed after {len(self.stages_run)} "
                f"stage(s); {self.abandoned[0]} could not fit, "
                "so the deadline was unrealistic, not the "
                "system slow, which are different bugs"
            )
        return (
            f"completed in {self.spent} of {self.total_budget}, "
            f"{self.remaining()} to spare; the whole chain "
            "honored the caller's clock"
        )

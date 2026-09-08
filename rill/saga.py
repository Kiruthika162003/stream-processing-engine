"""Saga: a long transaction as local steps, each undone in reverse when one fails.

Some transactions span services that cannot hold a lock across
all of them, so a saga replaces the single atomic commit with a
chain of local steps, each paired with a compensating action that
undoes it. The steps run forward, and if one fails the saga does
not roll back a shared transaction, there is none; it runs the
compensations for the steps that already completed. The order
those compensations run is the whole correctness of the pattern:
they must run in reverse of the forward order, because a later
step usually depends on an earlier one, and undoing the earlier
one first, refunding the charge before reversing the shipment
that the charge paid for, leaves the world in a state neither the
saga nor the services expected. Only the steps that actually
completed get compensated; a step that failed never happened and
a step never reached needs no undo. This module runs the forward
chain, stops at the first failure, and emits the compensations in
strict reverse order for exactly the completed prefix, so the
LIFO discipline the pattern lives or dies by is a checkable
sequence rather than a convention someone remembers to follow.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

COMMITTED = "committed"
COMPENSATED = "compensated"


@dataclass(frozen=True)
class SagaRun:
    status: str
    completed: tuple[str, ...]
    compensated: tuple[str, ...]
    failed_at: str | None


@dataclass(frozen=True)
class Saga:
    steps: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.steps:
            raise Invalid("a saga needs at least one step")

    def execute(self, succeeds: tuple[bool, ...]) -> SagaRun:
        if len(succeeds) != len(self.steps):
            raise Invalid("need one success flag per step")
        completed: list[str] = []
        for step, ok in zip(self.steps, succeeds, strict=True):
            if not ok:
                compensated = tuple(reversed(completed))
                return SagaRun(
                    status=COMPENSATED,
                    completed=tuple(completed),
                    compensated=compensated,
                    failed_at=step,
                )
            completed.append(step)
        return SagaRun(
            status=COMMITTED,
            completed=tuple(completed),
            compensated=(),
            failed_at=None,
        )

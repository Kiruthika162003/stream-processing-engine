"""Metastable failure: the outage that stays down after its cause is gone.

The cruelest distributed failure is the one that does not
recover when you fix it: a trigger pushes the system into a
state where its own load sustains the failure, so removing the
trigger changes nothing because the load is now the trigger.
A queue backs up, timeouts fire, clients retry, retries deepen
the backup, and the original slow disk that started it can be
replaced entirely while the system stays pinned down by the
retries it is still generating. The model captures the two
states, a stable healthy equilibrium and a stable failed one,
and the fact that the path back is not the path in: escaping
metastability needs load shed below the healthy threshold, not
merely below the trigger, because the system must be pushed
back across a lower boundary than the one it crossed. The
diagnosis the model prints is the one teams miss for hours,
the cause is gone and the effect remains, so stop looking for
a fresh cause and start shedding load.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class MetastableSystem:
    healthy_threshold: int
    amplification: float
    load: int = 0
    state: str = "healthy"

    def __post_init__(self) -> None:
        if self.healthy_threshold < 1:
            raise Invalid("a threshold is positive")
        if self.amplification <= 1:
            raise Invalid(
                "without amplification above one there is no "
                "metastability, only ordinary overload"
            )

    def offer(self, external_load: int) -> str:
        if external_load < 0:
            raise Invalid("load is nonnegative")
        if self.state == "failed":
            self.load = int(
                external_load
                + (self.load - self.healthy_threshold)
                * self.amplification
            )
            return (
                f"load {self.load} sustained by retries; the "
                "trigger is gone and the effect remains"
            )
        self.load = external_load
        if self.load > self.healthy_threshold * 2:
            self.state = "failed"
            return (
                f"tipped into the failed equilibrium at load "
                f"{self.load}; now its own load holds it down"
            )
        return f"healthy at load {self.load}"

    def shed_to(self, shed_target: int) -> str:
        if self.state != "failed":
            return "already healthy; nothing to escape"
        if shed_target >= self.healthy_threshold:
            return (
                f"shed to {shed_target} did nothing: still at "
                f"or above the healthy threshold "
                f"{self.healthy_threshold}; the path back is "
                "not the path in, and you must cross a lower "
                "boundary than the one you crossed"
            )
        self.state = "healthy"
        self.load = shed_target
        return (
            f"recovered: shed below {self.healthy_threshold} "
            f"to {shed_target}, back across the lower boundary "
            "metastability demands"
        )

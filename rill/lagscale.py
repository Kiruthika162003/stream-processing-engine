"""Scaling on lag: the worker you add must outrun the state it moves.

Stateless autoscaling is a thermostat; stateful autoscaling
is a loan application, because adding a worker to a stateful
stage triggers the moving day, keys and their state
migrating to the newcomer, and during the move the stage
drains slower, not faster. The decision is therefore an
inequality, not a threshold: scale up only when the lag the
extra worker will drain over its lifetime exceeds the lag
the migration will add while it happens, and the module
computes both sides with the numbers it is given, migration
ticks from state moved, drain gain from the new steady rate.
The refusal case is the one thermostats cannot express: lag
is high, the team is anxious, and the arithmetic says the
move costs more than it drains, scale later or scale by
more, because one worker's migration paid twice is worse
than none.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class ScaleDecision:
    current_lag: int
    arrival_rate: int
    drain_per_worker: int
    workers: int
    state_move_ticks: int
    horizon: int

    def __post_init__(self) -> None:
        if min(
            self.arrival_rate,
            self.drain_per_worker,
            self.workers,
            self.horizon,
        ) < 1:
            raise Invalid("rates, workers, horizon: all positive")
        if self.current_lag < 0 or self.state_move_ticks < 0:
            raise Invalid("lag and move cost cannot be negative")

    def lag_added_by_migration(self) -> int:
        return self.arrival_rate * self.state_move_ticks

    def lag_drained_by_newcomer(self) -> int:
        return self.drain_per_worker * self.horizon

    def verdict(self) -> str:
        added = self.lag_added_by_migration()
        drained = self.lag_drained_by_newcomer()
        current_drain = self.workers * self.drain_per_worker
        if current_drain >= self.arrival_rate and (
            self.current_lag == 0
        ):
            return (
                "holding at zero lag; a scale-up here is "
                "anxiety, not arithmetic"
            )
        if drained > added:
            surplus = drained - added
            return (
                f"SCALE UP: the newcomer drains {drained} "
                f"over the horizon against {added} added by "
                f"its own migration, {surplus} net; the loan "
                "pays for itself"
            )
        return (
            f"HOLD: migration adds {added} while the "
            f"newcomer only drains {drained} over the "
            "horizon; the move costs more than it drains, "
            "so scale later or scale by more, because one "
            "migration paid twice is worse than none"
        )

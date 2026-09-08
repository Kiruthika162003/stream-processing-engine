"""Checkpoint interval: too often wastes time saving, too rarely wastes it replaying.

How frequently to checkpoint a long-running job is a balance
nobody tunes by intuition well. Each checkpoint costs a fixed
amount of paused, non-productive time, so checkpointing often
spends a large fraction of the run just saving state. Checkpoint
rarely and the saving overhead vanishes, but a failure now
replays everything since the last checkpoint, on average half an
interval of work, so the recovery cost grows with the interval.
The wasted fraction of the run is therefore the checkpoint cost
over the interval plus the interval over twice the mean time
between failures, a sum that is large at both ends and has a
minimum in the middle. Setting the derivative to zero gives
Young's formula: the optimal interval is the square root of twice
the checkpoint cost times the mean time between failures, the
point where the marginal cost of one more checkpoint equals the
marginal replay it saves. Below it you overpay for saving, above
it you overpay for replay, and the formula is the trough between.
This module computes the waste rate for any interval and the
optimal interval, so the balance is a minimized number rather
than a guess between checkpointing constantly and never.
"""

from __future__ import annotations

import math

from rill.errors import Invalid


def waste_rate(interval: float, checkpoint_cost: float, mtbf: float) -> float:
    if interval <= 0 or checkpoint_cost <= 0 or mtbf <= 0:
        raise Invalid("interval, cost, and mtbf must be positive")
    return checkpoint_cost / interval + interval / (2 * mtbf)


def optimal_interval(checkpoint_cost: float, mtbf: float) -> float:
    if checkpoint_cost <= 0 or mtbf <= 0:
        raise Invalid("cost and mtbf must be positive")
    return math.sqrt(2 * checkpoint_cost * mtbf)

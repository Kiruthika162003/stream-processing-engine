"""Power of two choices: one extra probe turns a tall peak into a nearly flat one.

Routing each item to a random worker balances the average load
perfectly and the maximum load terribly, because randomness
clumps: with as many items as workers the busiest worker ends up
carrying a stack that grows like log n over log log n, tall
enough that the peak, not the average, is what tips over. The
power of two choices is the cheapest fix in distributed systems.
Instead of picking one worker at random, pick two and send the
item to the less loaded of them, and the maximum load collapses
from that logarithmic peak to something that grows like log log
n, an exponential improvement bought with exactly one extra
probe and one comparison per item. The intuition is that a single
random choice can always land on an already-tall pile, while
requiring an item to lose a race between two piles makes it very
unlikely to keep landing on the tallest, so the tall piles stop
growing. This module drops items into bins under one choice and
under two, taking its randomness from an injected source, and
reports the maximum load, so the flattening the second probe buys
is a measured height difference and not a citation.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


def max_load(
    balls: int, bins: int, choices: int, pick: Callable[[int], int]
) -> int:
    if balls < 0 or bins < 1:
        raise Invalid("balls non-negative and bins positive")
    if choices < 1:
        raise Invalid("need at least one choice")
    load = [0] * bins
    for _ in range(balls):
        candidates = [pick(bins) for _ in range(choices)]
        target = min(candidates, key=lambda index: load[index])
        load[target] += 1
    return max(load)


def imbalance(balls: int, bins: int, choices: int, pick: Callable[[int], int]) -> int:
    peak = max_load(balls, bins, choices, pick)
    average = balls // bins if bins else 0
    return peak - average

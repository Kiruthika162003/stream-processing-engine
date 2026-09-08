"""Weighted reservoir sampling: a uniform sample bent toward weight, in one pass.

Plain reservoir sampling gives every item the same chance, which
is wrong when items carry weights, a request that should be
sampled in proportion to its cost, an event weighted by its
value. Weighting the sample without a second pass or a known
total is the trick, and the A-Res algorithm does it with a key.
For each item draw a uniform random number and raise it to the
power one over the item's weight; a heavier weight pulls that key
closer to one, so the item is more likely to sit among the
largest keys. Keep the k items with the largest keys in a small
heap, and when the stream ends the reservoir holds a sample where
each item's probability of inclusion is proportional to its
weight, achieved in a single streaming pass with memory for k and
no knowledge of the stream's length or its total weight. The key
transform is the whole idea, turning multiplicative weights into
comparable draws so a simple keep-the-largest selection produces
the weighted distribution. This module keeps the heap and takes
its randomness from an injected source, so the weight-proportional
inclusion is a frequency a test can measure rather than a
probability argument taken on trust.
"""

from __future__ import annotations

import heapq
from collections.abc import Callable

from rill.errors import Invalid


def weighted_sample(
    items: list[tuple[str, int]],
    size: int,
    uniform: Callable[[], float],
) -> list[str]:
    if size < 1:
        raise Invalid("sample size must be positive")
    heap: list[tuple[float, str]] = []
    for name, weight in items:
        if weight <= 0:
            raise Invalid("weights must be positive")
        key = uniform() ** (1.0 / weight)
        if len(heap) < size:
            heapq.heappush(heap, (key, name))
        elif key > heap[0][0]:
            heapq.heapreplace(heap, (key, name))
    return sorted(name for _, name in heap)

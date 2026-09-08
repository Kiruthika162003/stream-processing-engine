"""Misra-Gries: finding the frequent items with k counters, no misses but some false alarms.

Finding every item that makes up more than a one-in-k fraction of
a stream, the heavy hitters, exactly needs a counter per distinct
item, which is unbounded. Misra-Gries does it with only k minus
one counters by a decrement trick that generalizes the majority
vote. Each item either lands on a counter it already owns and
increments it, or claims a free counter, or, when all counters are
taken by other items, causes every counter to be decremented by
one, dropping any that reach zero. The effect is that an item's
counter survives only if it appeared often enough to outlast the
decrements caused by the others, so any item that truly exceeds
the one-in-k fraction cannot be decremented away and is guaranteed
to still hold a counter at the end: no true heavy hitter is
missed. The catch is the other direction. A counter can survive
without its item being a real heavy hitter, because the decrements
did not happen to reach it, so the surviving counters are a
superset of the true answer and every candidate must be verified
with a second exact count before it is trusted. That is the shape
of the guarantee, no false negatives and possible false
positives, the same one-sided error the count-min sketch and the
majority vote carry. This module runs the counters and reports the
candidate set.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class MisraGries:
    k: int
    _counters: dict[str, int] = field(default_factory=dict)
    _seen: int = 0

    def __post_init__(self) -> None:
        if self.k < 2:
            raise Invalid("k must be at least two")

    def observe(self, item: str) -> None:
        self._seen += 1
        if item in self._counters:
            self._counters[item] += 1
        elif len(self._counters) < self.k - 1:
            self._counters[item] = 1
        else:
            for key in list(self._counters):
                self._counters[key] -= 1
                if self._counters[key] == 0:
                    del self._counters[key]

    def candidates(self) -> set[str]:
        return set(self._counters)

    def seen(self) -> int:
        return self._seen

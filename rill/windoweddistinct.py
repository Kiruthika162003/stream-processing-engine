"""Sliding window distinct: how many unique values in the last N, maintained not recomputed.

Counting the distinct values in the last N events, unique users in
the last hour, distinct error codes in the last thousand requests,
is easy to recompute from scratch each step and wasteful to,
because almost nothing changed: one value entered and one left. A
sliding window distinct counter maintains the answer incrementally
with a multiset. It keeps a count per value currently in the
window and a running total of how many values have a positive
count, which is the distinct count. Adding a value that was absent
raises the distinct count; adding one already present just bumps
its multiplicity. When the window slides and the oldest value
leaves, its count drops, and only if that count reaches zero does
the distinct count fall, because a value with other copies still
in the window is still present. So each step is a constant amount
of work regardless of the window size, where recomputing the
distinct set is linear in the window every time. The multiset is
the whole trick: without the per-value counts you cannot tell
whether an evicted value's departure actually removed it or merely
one of its copies. This module maintains the window and the
distinct count, checked against a recompute, so the incremental
count is correct as well as constant-time.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class WindowedDistinct:
    window: int
    _buffer: deque[str] = field(default_factory=deque)
    _counts: dict[str, int] = field(default_factory=dict)
    _distinct: int = 0

    def __post_init__(self) -> None:
        if self.window < 1:
            raise Invalid("window must be positive")

    def add(self, value: str) -> None:
        self._buffer.append(value)
        if self._counts.get(value, 0) == 0:
            self._distinct += 1
        self._counts[value] = self._counts.get(value, 0) + 1
        if len(self._buffer) > self.window:
            old = self._buffer.popleft()
            self._counts[old] -= 1
            if self._counts[old] == 0:
                self._distinct -= 1

    def distinct(self) -> int:
        return self._distinct

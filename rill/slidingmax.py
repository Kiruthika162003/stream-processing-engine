"""Sliding window maximum: a monotonic deque touches each element once, not per window.

Reporting the maximum of the last k events on every new event is
the naive O(k) rescan per step, O(nk) over the stream, and it is
wasteful because almost every rescan re-examines the same values
the last one did. The monotonic deque removes the waste. It keeps
only the values that could still become the maximum, in
decreasing order, so the front is always the current window's max.
A new value pops every smaller value off the back before it joins,
because a value smaller than one that arrived later can never be
the max while that later one is in the window, and the front is
dropped once its index falls out of the window. The accounting
that makes it fast is that every element is pushed exactly once
and popped at most once across the whole stream, so the total
work is linear no matter how large the window, and the per-step
cost is O(1) amortized rather than O(k). This module runs the
deque, answers the window maximum, and counts the total pushes
and pops, so the once-each bound is a measured total set against
the O(nk) rescan it replaces.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from rill.errors import Invalid, Missing


@dataclass
class SlidingMax:
    window: int
    _deque: deque[tuple[int, int]] = field(default_factory=deque)
    _count: int = 0
    _ops: int = 0

    def __post_init__(self) -> None:
        if self.window < 1:
            raise Invalid("window must be positive")

    def push(self, value: int) -> None:
        index = self._count
        while self._deque and self._deque[-1][1] <= value:
            self._deque.pop()
            self._ops += 1
        self._deque.append((index, value))
        self._ops += 1
        while self._deque[0][0] <= index - self.window:
            self._deque.popleft()
            self._ops += 1
        self._count += 1

    def maximum(self) -> int:
        if not self._deque:
            raise Missing("no values in the window yet")
        return self._deque[0][1]

    def total_ops(self) -> int:
        return self._ops

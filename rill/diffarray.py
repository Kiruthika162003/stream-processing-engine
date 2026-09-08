"""Difference array: adding to a whole range in one step, materialized once at the end.

Applying many range updates to an array, add this to positions
five through five hundred, subtract that from ten through fifty,
the way you might accumulate load contributions across time
windows, is wasteful done directly, because each update touches
every element in its range and a thousand wide updates cost a
thousand ranges of work. The difference array makes each range
update O(1). It stores not the array but the differences between
consecutive elements, and adding a delta to a half-open range is
two point edits: add the delta where the range begins, marking
where the elevated level starts, and subtract it where the range
ends, marking where it stops. No matter how wide the range, that
is two touches. After all the updates are recorded, one prefix-sum
pass over the difference array reconstructs the final values,
because the prefix sum accumulates each start's delta from its
position onward and each end's negation cancels it beyond the
range. So K range updates plus a materialize cost K plus n rather
than K times the range width, the right structure when updates are
batched and the array is read once at the end. This module records
range updates in constant time and materializes the array in one
pass, checked against a naive per-element application.
"""

from __future__ import annotations

from rill.errors import Invalid


class DifferenceArray:
    def __init__(self, size: int) -> None:
        if size < 1:
            raise Invalid("size must be positive")
        self.size = size
        self._diff = [0] * (size + 1)

    def add_range(self, lo: int, hi: int, delta: int) -> None:
        if not 0 <= lo <= hi <= self.size:
            raise Invalid(f"range [{lo}, {hi}) out of bounds")
        self._diff[lo] += delta
        self._diff[hi] -= delta

    def materialize(self) -> list[int]:
        result = []
        running = 0
        for index in range(self.size):
            running += self._diff[index]
            result.append(running)
        return result

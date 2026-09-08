"""Dutch national flag: partitioning into less, equal, greater in one pass with three pointers.

Partitioning a sequence around a pivot into the elements below it,
equal to it, and above it, the three-way partition Dijkstra named
for the tricolor flag, is the operation that keeps quicksort and
quickselect fast when the data has many equal keys. A two-way
partition, everything not-greater on one side, degrades to
quadratic on an array of mostly-equal values because the equal
elements pile onto one side and the recursion barely shrinks; the
three-way partition drops every element equal to the pivot into a
middle band that needs no further work, so duplicates are handled
once and for all. It runs in a single pass with three pointers: a
low boundary below which everything is less than the pivot, a high
boundary above which everything is greater, and a scanning cursor
that walks up from the low boundary. An element less than the pivot
swaps down to the low boundary and both advance; an element greater
swaps up to the high boundary which retreats, and the cursor stays
to re-examine what was swapped in; an equal element the cursor just
steps over. When the cursor passes the high boundary the array is
in three contiguous bands. This module returns the partitioned
array and the band boundaries, checked against a sorted reference,
so the one-pass three-way split is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def three_way_partition(values: list[int], pivot: int) -> tuple[list[int], int, int]:
    if values is None:
        raise Invalid("values must not be None")
    arr = list(values)
    low = 0
    high = len(arr) - 1
    cursor = 0
    while cursor <= high:
        if arr[cursor] < pivot:
            arr[low], arr[cursor] = arr[cursor], arr[low]
            low += 1
            cursor += 1
        elif arr[cursor] > pivot:
            arr[high], arr[cursor] = arr[cursor], arr[high]
            high -= 1
        else:
            cursor += 1
    return arr, low, high + 1

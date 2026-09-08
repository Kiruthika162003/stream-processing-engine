"""Heap sort: the sort with a guaranteed n log n worst case and no extra array.

Among comparison sorts, heap sort occupies a specific corner:
quicksort is fast on average but has a quadratic worst case an
adversary can trigger, merge sort is n log n always but needs a
second array of scratch space, and heap sort is n log n in the
worst case and sorts in place, needing only a constant amount of
extra memory. It works in two phases over the array itself. First
it arranges the array into a binary max-heap, where every parent is
at least its two children, by sifting each internal node down into
place from the bottom up, which takes linear time. Then it
repeatedly swaps the maximum, sitting at the root, to the end of
the unsorted region, shrinks that region by one, and sifts the new
root down to restore the heap, so the largest remaining element
lands in its final position each step. After n such extractions the
array is sorted, and every operation happened inside the original
array. The trade for its guarantees is a worse constant factor and
poor cache behavior compared to quicksort, since the sift-down
jumps around the array rather than scanning it, so heap sort is the
choice when the worst case must be bounded and memory is tight
rather than when raw average speed is the goal. This module heap
sorts in place, checked against the builtin sort, so the in-place
guaranteed-n-log-n sort is correct.
"""

from __future__ import annotations

from rill.errors import Invalid


def _sift_down(arr: list[int], start: int, size: int) -> None:
    root = start
    while True:
        child = 2 * root + 1
        if child >= size:
            return
        if child + 1 < size and arr[child + 1] > arr[child]:
            child += 1
        if arr[root] >= arr[child]:
            return
        arr[root], arr[child] = arr[child], arr[root]
        root = child


def heap_sort(values: list[int]) -> list[int]:
    if values is None:
        raise Invalid("values must not be None")
    arr = list(values)
    size = len(arr)
    for start in range(size // 2 - 1, -1, -1):
        _sift_down(arr, start, size)
    for end in range(size - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        _sift_down(arr, 0, end)
    return arr

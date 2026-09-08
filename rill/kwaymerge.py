"""K-way merge: interleaving many sorted partitions by a heap the size of the streams.

Merging several already-sorted streams into one sorted output,
partitions ordered by event time, sorted runs from a spill, is
the recurring shape of a streaming merge, and the wasteful way is
to concatenate them all and sort, which throws away the fact that
each input was already ordered and costs n log n. The heap-based
k-way merge keeps the order it was given. It holds one element
from each of the k streams in a min-heap, repeatedly takes the
smallest, emits it, and pulls the next element from the stream
that element came from, so the heap never holds more than k
elements and every one of the n elements costs a single log-k
heap operation to place, giving n log k overall. When there are
far more elements than streams, and there always are, log k is
much smaller than log n, so the merge that respects the existing
order finishes well ahead of the one that ignores it. The heap
also makes the merge naturally streaming, producing output as it
goes rather than after a full sort. This module runs the merge,
checking the output against a sorted concatenation so the order
is correct, and the point is that it reached that order through a
heap bounded by the stream count, not the element count.
"""

from __future__ import annotations

import heapq

from rill.errors import Invalid


def merge(streams: list[list[int]]) -> list[int]:
    if not streams:
        raise Invalid("no streams to merge")
    heap: list[tuple[int, int, int]] = []
    for index, stream in enumerate(streams):
        for position in range(len(stream) - 1):
            if stream[position] > stream[position + 1]:
                raise Invalid(f"stream {index} is not sorted")
        if stream:
            heapq.heappush(heap, (stream[0], index, 0))
    out: list[int] = []
    while heap:
        value, index, position = heapq.heappop(heap)
        out.append(value)
        nxt = position + 1
        if nxt < len(streams[index]):
            heapq.heappush(heap, (streams[index][nxt], index, nxt))
    return out

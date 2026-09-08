"""Mo's algorithm: answer many range queries offline by ordering them cleverly.

Given an array and many queries, each asking something about a
range, like how many distinct values it holds, the direct approach
recomputes each range from scratch, which is the range width times
the query count. Mo's algorithm does better when the queries are all
known in advance, offline: it keeps a current window and a running
answer, and moves the window's two ends to match the next query,
adding and removing one element at a time and updating the answer
incrementally. The order the queries are processed in is everything,
because it decides how far the ends travel in total. Mo's order
sorts the queries into blocks by the left end, the block width the
square root of the array length, and within a block by the right
end. With that order the right end sweeps monotonically across each
block, moving the array length per block over all blocks, and the
left end wanders only within a block per query. The totals work out
to the array length plus the query count, times the square root of
the array length, far below recomputing each range when there are
many queries. The one requirement is that the per-element add and
remove be cheap, constant or nearly so, since the whole cost is
counted in those steps. This module runs Mo's algorithm for the
count-distinct query with a frequency table whose add and remove
are constant time, and a test checks every answer against a brute
recomputation, so the reordering is confirmed to preserve the
answers while cutting the work.
"""

from __future__ import annotations

import math

from rill.errors import Invalid


def count_distinct_queries(
    values: list[int], queries: list[tuple[int, int]]
) -> list[int]:
    if values is None or queries is None:
        raise Invalid("values and queries must not be None")
    n = len(values)
    for lo, hi in queries:
        if lo < 0 or hi >= n or lo > hi:
            raise Invalid("each query must be a valid range within the array")
    block = max(1, math.isqrt(n))

    def order_key(indexed: tuple[int, tuple[int, int]]) -> tuple[int, int]:
        _, (lo, hi) = indexed
        return (lo // block, hi)

    ordered = sorted(enumerate(queries), key=order_key)
    answers = [0] * len(queries)
    freq: dict[int, int] = {}
    distinct = 0
    cur_lo, cur_hi = 0, -1
    for original, (lo, hi) in ordered:
        while cur_hi < hi:
            cur_hi += 1
            v = values[cur_hi]
            if freq.get(v, 0) == 0:
                distinct += 1
            freq[v] = freq.get(v, 0) + 1
        while cur_lo > lo:
            cur_lo -= 1
            v = values[cur_lo]
            if freq.get(v, 0) == 0:
                distinct += 1
            freq[v] = freq.get(v, 0) + 1
        while cur_hi > hi:
            v = values[cur_hi]
            freq[v] -= 1
            if freq[v] == 0:
                distinct -= 1
            cur_hi -= 1
        while cur_lo < lo:
            v = values[cur_lo]
            freq[v] -= 1
            if freq[v] == 0:
                distinct -= 1
            cur_lo += 1
        answers[original] = distinct
    return answers

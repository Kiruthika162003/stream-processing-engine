"""Delta plus varint: sorted offsets shrink by their gaps, not their magnitude.

A log or an index stores a long list of sorted offsets, each a
large absolute number that would take a fixed eight bytes stored
raw. Two encodings stacked together shrink it dramatically. Delta
encoding stores the first offset and then only the difference
from the previous one, and because the offsets are sorted those
differences are small even when the offsets themselves are near
the top of the range. Variable-length integer encoding then
spends bytes in proportion to a number's magnitude, one byte for
values under 128, two under 16384, and so on, so the small deltas
cost one or two bytes where the raw offsets cost eight. Together
they turn a list whose values are huge but whose gaps are tiny
into a stream of one-byte numbers, which is exactly the shape a
monotonic offset column has. The saving depends entirely on the
gaps staying small; a list with occasional large jumps pays more
for those deltas, and an unsorted list gets no benefit at all
because its differences are as large as its values. This module
delta-encodes, sizes the varint stream, and compares it to the
raw width, so the compression is a measured ratio on data whose
gaps are what actually determine it.
"""

from __future__ import annotations

from itertools import pairwise

from rill.errors import Invalid


def delta_encode(offsets: list[int]) -> list[int]:
    if not offsets:
        raise Invalid("no offsets")
    deltas = [offsets[0]]
    for previous, current in pairwise(offsets):
        if current < previous:
            raise Invalid("offsets must be sorted ascending")
        deltas.append(current - previous)
    return deltas


def varint_size(value: int) -> int:
    if value < 0:
        raise Invalid("varint encodes non-negative integers")
    size = 1
    while value >= 128:
        value >>= 7
        size += 1
    return size


def encoded_size(offsets: list[int]) -> int:
    return sum(varint_size(delta) for delta in delta_encode(offsets))


def raw_size(offsets: list[int], width: int = 8) -> int:
    if width <= 0:
        raise Invalid("width must be positive")
    return len(offsets) * width

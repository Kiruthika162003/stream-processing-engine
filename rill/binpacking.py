"""Bin packing: sorting the items largest first fits them in fewer bins.

Packing items of varying size into the fewest bins of fixed
capacity is NP-hard exactly and well served by a greedy first-fit:
walk the items, drop each into the first bin it fits, and open a
new bin only when none has room. As with scheduling, the order the
items are considered decides how good the packing is, and for the
same reason. Consider the items smallest first and the small ones
scatter across many bins leaving each with an awkward remainder,
and then the large items arriving late will not fit those
remainders and each opens a bin of its own, wasting the space the
small items fragmented. First-fit-decreasing sorts the items
largest first, so the big items are placed into empty bins while
there is room to plan around them, and the small items at the end
slot into the gaps the big ones left, which is exactly the space
they fit. The result packs into measurably fewer bins, with a
worst case bounded near eleven-ninths of optimal against first-fit
in an arbitrary order which can do much worse. This module runs
first-fit in both orders and reports the bins used, so the saving
from placing the large items first is a measured difference rather
than an approximation ratio quoted from a proof.
"""

from __future__ import annotations

from rill.errors import Invalid


def _first_fit(items: list[int], capacity: int) -> int:
    bins: list[int] = []
    for item in items:
        for index in range(len(bins)):
            if bins[index] + item <= capacity:
                bins[index] += item
                break
        else:
            bins.append(item)
    return len(bins)


def first_fit(items: list[int], capacity: int) -> int:
    _validate(items, capacity)
    return _first_fit(items, capacity)


def first_fit_decreasing(items: list[int], capacity: int) -> int:
    _validate(items, capacity)
    return _first_fit(sorted(items, reverse=True), capacity)


def _validate(items: list[int], capacity: int) -> None:
    if capacity <= 0:
        raise Invalid("capacity must be positive")
    if any(item <= 0 or item > capacity for item in items):
        raise Invalid("each item must fit within a positive capacity")

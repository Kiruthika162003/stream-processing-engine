"""Merge sort: n log n always and stable, the property heap sort and quicksort give up.

Merge sort splits the input in half, sorts each half, and merges
the two sorted halves into one, which is n log n in every case, not
just on average, because the split is always even and the merge is
always linear. Its distinguishing property among the n-log-n sorts
is stability: when two elements compare equal, merge sort keeps the
one that came first in the input ahead of the other, and heap sort
and quicksort do not, because their swaps move equal elements past
each other arbitrarily. Stability matters whenever the elements are
records sorted by a key, because a stable sort by one key preserves
an earlier ordering by another, so sorting by date and then stably
by name leaves records with the same name in date order, which an
unstable sort would scramble. The merge is where stability is won
or lost: when the two halves' fronts compare equal, taking from the
left half first, the one that was earlier in the input, is what
preserves order, and taking from the right first would break it on
exactly the equal keys. The cost of the guarantees is a scratch
array the size of the input, the space heap sort avoids. This
module merge sorts by a key with the left-first tie rule, and a
test sorts keyed records to confirm equal keys keep their input
order, so the stability is demonstrated rather than assumed.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


def merge_sort(
    items: list[tuple[int, str]], key: Callable[[tuple[int, str]], int] | None = None
) -> list[tuple[int, str]]:
    if items is None:
        raise Invalid("items must not be None")
    keyer = key if key is not None else (lambda item: item[0])
    return _sort(list(items), keyer)


def _sort(
    items: list[tuple[int, str]], key: Callable[[tuple[int, str]], int]
) -> list[tuple[int, str]]:
    if len(items) <= 1:
        return items
    mid = len(items) // 2
    left = _sort(items[:mid], key)
    right = _sort(items[mid:], key)
    merged: list[tuple[int, str]] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged

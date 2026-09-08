"""Next permutation: step to the next arrangement in lexicographic order, in place.

Generating permutations one at a time in dictionary order, without
holding them all in memory, is what the next-permutation step does:
given an arrangement, it produces the smallest arrangement that is
lexicographically larger, or reports that the current one is the
largest, the fully descending sequence. The algorithm, due to
Narayana centuries before it was rediscovered for computers, is a
precise little dance over the sequence from the right. First find the
pivot, the rightmost position whose element is smaller than the one
just after it; everything to its right is a descending run, already
the largest order for those elements, so the pivot is where the
increase must happen. Then find, again from the right, the smallest
element in that descending tail that still exceeds the pivot, and
swap the two. The pivot position now holds the next-larger value, and
the tail to its right is still descending, so reversing that tail
turns it into the smallest, ascending, order, completing the smallest
possible increase. When no pivot exists the whole sequence descends,
it is the last permutation, and the convention is to wrap by
reversing it back to the sorted first permutation and report the
wrap. The finding worth stating is that only a swap and a reversal,
both touching a suffix, are needed per step, so iterating through all
permutations costs amortized constant work each, no factorial memory.
This module steps to the next permutation in place, and a test walks
the full cycle from the sorted sequence and checks it visits every
distinct permutation exactly once before wrapping, so the ordering is
confirmed complete.
"""

from __future__ import annotations

from rill.errors import Invalid


def next_permutation(items: list[int]) -> bool:
    if items is None:
        raise Invalid("items must not be None")
    n = len(items)
    pivot = n - 2
    while pivot >= 0 and items[pivot] >= items[pivot + 1]:
        pivot -= 1
    if pivot < 0:
        items.reverse()
        return False
    successor = n - 1
    while items[successor] <= items[pivot]:
        successor -= 1
    items[pivot], items[successor] = items[successor], items[pivot]
    _reverse_suffix(items, pivot + 1)
    return True


def _reverse_suffix(items: list[int], start: int) -> None:
    end = len(items) - 1
    while start < end:
        items[start], items[end] = items[end], items[start]
        start += 1
        end -= 1

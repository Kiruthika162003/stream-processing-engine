"""Radix sort: sorting integers digit by digit, and why each pass must be stable.

Counting sort is linear but wants a small value range; radix sort
extends it to large integers by sorting on one digit at a time. It
makes a pass per digit position, from least significant to most,
and on each pass sorts the numbers by just that digit using a
stable counting sort. The property that makes the whole thing work,
and the one that quietly breaks it if omitted, is stability. When
the pass on a higher digit puts two numbers with the same higher
digit in some order, that order must be the one the lower digits
already established, so a stable sort on the current digit is
required to preserve the work of the previous passes. Sort each
digit with an unstable method and the earlier digits' ordering is
scrambled, and the result is wrong even though every individual
pass sorted correctly. With stable passes, after the most
significant digit is processed the numbers are fully sorted, in a
number of passes equal to the digit count times the cost of one
counting sort, linear in the element count for a fixed width. So
radix sort trades the comparison sort's generality for linear time
on fixed-width integer keys, exactly the shape of ids, fixed-point
timestamps, and packed keys. This module sorts by least-
significant-digit radix with stable digit passes, checked against
the builtin sort, so the correctness that depends on stability is
a test.
"""

from __future__ import annotations

from rill.errors import Invalid


def radix_sort(values: list[int], base: int = 10) -> list[int]:
    if base < 2:
        raise Invalid("base must be at least two")
    if any(value < 0 for value in values):
        raise Invalid("radix sort here handles non-negative integers")
    if not values:
        return []
    result = list(values)
    largest = max(result)
    place = 1
    while place <= largest:
        buckets: list[list[int]] = [[] for _ in range(base)]
        for value in result:
            buckets[(value // place) % base].append(value)
        result = [value for bucket in buckets for value in bucket]
        place *= base
    return result

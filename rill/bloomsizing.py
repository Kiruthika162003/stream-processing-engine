"""Bloom sizing: how many bits and hashes a target false-positive rate actually costs.

A Bloom filter's false-positive rate is not free to choose; it is
bought with bits, and the arithmetic that connects them is worth
computing rather than guessing. For n expected elements and m bits
of storage, the optimal number of hash functions is m over n times
the natural log of two, and at that optimum the false-positive
rate is one half raised to the number of hashes. Inverting that
gives the bits needed for a target rate: m is minus n times the
log of the target rate over the square of the log of two, which
works out to about 9.6 bits per element for a one-percent rate and
about 14.4 for a tenth of a percent, so each additional order of
magnitude of accuracy costs a fixed increment of bits per element,
not a multiplication. The number of hashes matters too, and in
both directions: too few and the bits are underused so the rate is
worse than it could be, too many and the filter fills up faster so
the rate climbs again, with the optimum in between. The practical
reading is that a Bloom filter's memory is a direct function of
how many elements and how wrong you can tolerate being, computable
before allocating anything. This module computes the bits, the
optimal hash count, and the resulting rate, so the sizing is a
number rather than a default someone copied.
"""

from __future__ import annotations

import math

from rill.errors import Invalid


def bits_for(elements: int, target_rate: float) -> int:
    if elements < 1:
        raise Invalid("elements must be positive")
    if not 0.0 < target_rate < 1.0:
        raise Invalid("target rate is a fraction in (0, 1)")
    m = -elements * math.log(target_rate) / (math.log(2) ** 2)
    return math.ceil(m)


def optimal_hashes(bits: int, elements: int) -> int:
    if bits < 1 or elements < 1:
        raise Invalid("bits and elements must be positive")
    return max(1, round(bits / elements * math.log(2)))


def false_positive_rate(bits: int, elements: int, hashes: int) -> float:
    if bits < 1 or elements < 1 or hashes < 1:
        raise Invalid("bits, elements, and hashes must be positive")
    return (1 - math.exp(-hashes * elements / bits)) ** hashes

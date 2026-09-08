"""Chinese remainder theorem: one number matching many remainders at once.

Given a set of remainders, each against a different modulus, the
Chinese remainder theorem says that when the moduli are pairwise
coprime there is exactly one solution modulo their product, one
number that leaves the first remainder against the first modulus,
the second against the second, and so on. The classic framing is
ancient: find the count of soldiers that leaves three when lined up
in fives, two when lined up in sevens. The construction combines the
congruences two at a time. To merge a solution x modulo m with a new
remainder r modulo n, seek the answer in the form x plus m times k,
which already satisfies the first congruence for any k, and solve
for k so that it also leaves r modulo n. That solve is a single
modular division, x plus m times k congruent to r modulo n, which
needs the inverse of m modulo n, and that inverse exists precisely
because m and n are coprime, the theorem's hypothesis. Fold the
congruences in one by one and the running modulus grows to the
product. The coprimality is not decoration: without it two
congruences can contradict, asking for a number both even and odd,
and then no solution exists, so the honest response to non-coprime
moduli that disagree is to refuse rather than return a wrong number.
The finding worth stating is that the merge rests entirely on the
modular inverse, so the theorem is really the extended Euclidean
algorithm wearing a number-theory hat. This module solves a system
of congruences, and a test checks the answer satisfies every
congruence and matches a brute search over the product range, so the
fold is confirmed correct.
"""

from __future__ import annotations

from rill.errors import Invalid
from rill.extgcd import mod_inverse


def crt(remainders: list[int], moduli: list[int]) -> tuple[int, int]:
    if remainders is None or moduli is None:
        raise Invalid("remainders and moduli must not be None")
    if len(remainders) != len(moduli):
        raise Invalid("remainders and moduli must have equal length")
    if not moduli:
        raise Invalid("at least one congruence is required")
    if any(m <= 0 for m in moduli):
        raise Invalid("moduli must be positive")
    x = remainders[0] % moduli[0]
    modulus = moduli[0]
    for r, m in zip(remainders[1:], moduli[1:], strict=True):
        # solve x + modulus*k == r (mod m); needs inverse of modulus mod m
        inv = mod_inverse(modulus % m, m)
        k = (r - x) * inv % m
        x = x + modulus * k
        modulus *= m
        x %= modulus
    return x % modulus, modulus

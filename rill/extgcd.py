"""Extended Euclid: the gcd plus the coefficients that give a modular inverse.

The Euclidean algorithm finds the greatest common divisor of two
numbers by replacing the larger with its remainder against the
smaller until one becomes zero, and the other is the gcd. The
extended version tracks, alongside the gcd, a pair of integers x
and y solving Bezout's identity, a times x plus b times y equals
the gcd, carried through the same recursion. Those coefficients are
what turn the gcd into a modular inverse. The inverse of a modulo m
is the number that multiplies a to one modulo m, and it exists if
and only if a and m are coprime, gcd one, because only then does
some combination of a and m reach one. When it exists, Bezout gives
a times x plus m times y equals one, so a times x is one modulo m,
and x reduced into the range zero to m minus one is the inverse.
The existence condition is not a technicality to gloss over: asking
for the inverse of a number sharing a factor with the modulus is a
question with no answer, and the honest thing is to refuse it rather
than return a wrong number. Modular inverses are the workhorse of
modular division, needed anywhere arithmetic is done modulo a prime,
from hashing to cryptography to combinatorics. This module computes
the extended gcd and the modular inverse, and a test checks the
inverse against Python's own pow with exponent minus one and
confirms that a non-coprime pair is refused, so both the value and
the existence rule are verified.
"""

from __future__ import annotations

from rill.errors import Invalid


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    return old_r, old_s, old_t


def gcd(a: int, b: int) -> int:
    return extended_gcd(a, b)[0]


def mod_inverse(a: int, m: int) -> int:
    if m <= 0:
        raise Invalid("modulus must be positive")
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        raise Invalid("no inverse exists when a and m share a factor")
    return x % m

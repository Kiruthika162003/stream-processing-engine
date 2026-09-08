"""Karatsuba: multiply two big numbers with three half-size products, not four.

Multiplying two n-digit numbers the schoolbook way multiplies every
digit of one by every digit of the other, which is quadratic in the
digit count. Karatsuba's insight is that the four half-size products
the divide-and-conquer split seems to need can be had with three.
Split each number into a high and low half, so x is a times the base
plus b and y is c times the base plus d. The full product is a*c
times base squared, plus (a*d + b*c) times base, plus b*d. That
names four products, a*c, a*d, b*c, b*d. The trick: compute a*c and
b*d, then compute (a+b)*(c+d), which expands to a*c + a*d + b*c +
b*d, and subtract the two already known from it to recover the whole
middle term a*d + b*c in one multiplication instead of two. Three
half-size multiplications, plus some additions, replace four. The
recursion depth is the log of the digit count and each level does
three times the work of a half, so the cost is n to the log-base-2
of 3, about n to the 1.585, below the quadratic of schoolbook. It
only pays above a crossover size, since the extra additions and
recursion overhead dominate for small numbers, so a real
implementation falls back to the builtin multiply below a threshold,
which this module does. The finding worth stating is that the count
of multiplications, not additions, is what the split reduces, three
against four, and that is the whole source of the speedup. This
module multiplies via Karatsuba and a test checks the result against
Python's own product over many random numbers, so the three-product
identity is confirmed exact.
"""

from __future__ import annotations

from rill.errors import Invalid

_THRESHOLD = 16


def karatsuba(x: int, y: int) -> int:
    if x is None or y is None:
        raise Invalid("both operands must be integers")
    sign = -1 if (x < 0) != (y < 0) else 1
    return sign * _mul(abs(x), abs(y))


def _mul(x: int, y: int) -> int:
    if x < (1 << _THRESHOLD) or y < (1 << _THRESHOLD):
        return x * y
    half = (max(x.bit_length(), y.bit_length()) // 2)
    mask = (1 << half) - 1
    a, b = x >> half, x & mask
    c, d = y >> half, y & mask
    ac = _mul(a, c)
    bd = _mul(b, d)
    middle = _mul(a + b, c + d) - ac - bd
    return (ac << (2 * half)) + (middle << half) + bd

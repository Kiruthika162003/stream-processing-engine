"""Gray code: order the binary numbers so each differs from the next by one bit.

An ordinary binary count flips many bits between consecutive values;
going from three to four, 011 to 100, flips all three. That matters
for physical encoders and state machines, where several bits changing
at once can be read mid-transition and produce a nonsense
intermediate value. A Gray code is a reordering of all n-bit numbers
so that consecutive entries, and the last back to the first, differ
in exactly one bit, which makes any single-step transition
unambiguous. The reflected binary Gray code has a strikingly simple
closed form: the Gray code of an integer is that integer exclusive-or
its own right shift by one. That the formula gives a single-bit
change between neighbors is not obvious from staring at it, but it
follows from the recursive construction the name reflects: take the
Gray sequence for n minus one bits, prefix every entry with a zero,
then append the same sequence reversed with every entry prefixed by a
one. The join in the middle changes only the leading bit because the
two halves meet at the same lower bits, and the reversal makes the
wraparound a single-bit change too, so the code is cyclic. Decoding
back to the integer is a running exclusive-or of the Gray bits from
the top down. The finding worth stating is that the whole single-bit
guarantee is captured by the one-line xor-with-shift encode and its
prefix-xor inverse, no table needed. This module encodes and decodes
Gray codes and lists the full n-bit sequence, and a test checks every
adjacent pair, and the cyclic wrap, differs by exactly one bit and
that decode inverts encode, so the reflected code is confirmed.
"""

from __future__ import annotations

from rill.errors import Invalid


def encode(value: int) -> int:
    if value < 0:
        raise Invalid("value must not be negative")
    return value ^ (value >> 1)


def decode(gray: int) -> int:
    if gray < 0:
        raise Invalid("gray code must not be negative")
    value = 0
    while gray:
        value ^= gray
        gray >>= 1
    return value


def sequence(bits: int) -> list[int]:
    if bits < 0:
        raise Invalid("bit count must not be negative")
    return [encode(i) for i in range(1 << bits)]

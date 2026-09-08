"""Luhn checksum: a check digit that catches every single-digit slip and almost every swap.

An identifier a human types or reads aloud, an account number, a
card, a meter id, needs a cheap guard against the two mistakes
people actually make: mistyping one digit, and transposing two
adjacent ones. The Luhn formula appends a check digit computed so
that a weighted sum of all the digits is a multiple of ten, where
every second digit from the right is doubled and its result folded
into a single digit if it exceeds nine. That doubling is what
gives the check its coverage. Any single wrong digit changes the
sum by an amount that cannot be a multiple of ten, so it always
fails the check and is caught. A transposition of two adjacent
digits changes the sum by the difference of their doubled and
undoubled contributions, which is nonzero and caught for every
pair except one, the swap of a zero and a nine, whose doubled
difference happens to land on a multiple of ten. So Luhn catches
all single-digit errors and all adjacent transpositions but the
one, a lot of protection for one appended digit and a sum anyone
can compute. This module validates a number and computes the
check digit, so the errors it catches and the single swap it
misses are demonstrable rather than folklore about check digits.
"""

from __future__ import annotations

from rill.errors import Invalid


def _digits(number: str) -> list[int]:
    if not number or not number.isdigit():
        raise Invalid("number must be a non-empty string of digits")
    return [int(char) for char in number]


def _weighted_sum(digits: list[int]) -> int:
    total = 0
    for position, digit in enumerate(reversed(digits)):
        if position % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total


def is_valid(number: str) -> bool:
    return _weighted_sum(_digits(number)) % 10 == 0


def check_digit(payload: str) -> int:
    digits = [*_digits(payload), 0]
    return (10 - _weighted_sum(digits) % 10) % 10

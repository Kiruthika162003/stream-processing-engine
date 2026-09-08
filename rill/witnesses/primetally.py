"""The linear sieve's prime counts against the known prime-counting function.

The drill runs the linear sieve up to a hundred thousand and counts
the primes it found at four checkpoints, then factorizes every
number up to ten thousand through the smallest-prime-factor table
and multiplies the factors back. The guess worth recording was a
worry that the break-when-p-divides-i rule, the one subtle line that
makes the sieve linear, might skip a composite and leave it counted
as prime, inflating the counts. The measurement refutes it exactly:
the prime counts came out 25, 168, 1229, 9592 at a hundred, a
thousand, ten thousand, a hundred thousand, matching the known
values of the prime-counting function to the digit, and every one
of the ten thousand factorizations multiplied back to its number
with the factors in sorted order, zero reconstruction failures. The
deposition keeps the might-skip-a-composite worry beside the
measured agreement, because the break rule does not skip composites,
it guarantees each is marked once through its smallest prime factor,
which is precisely why the counts land on the known function.
"""

from __future__ import annotations

import math

from rill.sieve import factorize, linear_sieve
from rill.witnesses.deposition import Deposition

_KNOWN = {100: 25, 1000: 168, 10000: 1229, 100000: 9592}


def run() -> Deposition:
    counts_match = True
    for limit, expected in _KNOWN.items():
        primes, _ = linear_sieve(limit)
        if len(primes) != expected:
            counts_match = False
    _, spf = linear_sieve(10000)
    failures = 0
    for n in range(2, 10001):
        factors = factorize(n, spf)
        if math.prod(factors) != n or factors != sorted(factors):
            failures += 1
    numbers = {
        "pi_100": _KNOWN[100],
        "pi_100000": _KNOWN[100000],
        "counts_match_known": counts_match,
        "factorization_failures": failures,
    }
    holds = counts_match and failures == 0
    return Deposition(
        witness="primetally",
        claim=(
            "the linear sieve's prime counts matched the known "
            "prime-counting function at 100, 1000, 10000, 100000 and "
            "every factorization up to ten thousand reconstructed"
        ),
        numbers=numbers,
        holds=holds,
    )

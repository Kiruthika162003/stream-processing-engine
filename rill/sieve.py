"""Linear sieve: primes up to n while marking each composite exactly once.

The sieve of Eratosthenes finds all primes up to n by crossing out
the multiples of each prime, which is n log log n, close to linear
but not quite, because a composite with several prime factors gets
crossed out once per distinct factor. The linear sieve, Euler's,
tightens that to strictly linear by arranging for each composite to
be crossed out exactly once, by its smallest prime factor. It walks
the numbers from two upward keeping the primes found so far. At i it
first records i as prime if nothing has marked it, then, for each
known prime p in increasing order, marks i times p as composite and
stores p as that product's smallest prime factor. The single subtle
rule that makes it linear is the break: as soon as p divides i, stop
the inner loop. Beyond that point i times a larger prime would have
p, not the larger prime, as its true smallest factor, so marking it
here would be marking it by the wrong factor and, worse, a second
time later. Stopping guarantees every composite is reached once,
through its smallest prime factor, which is why the total work is
linear. The stored smallest-prime-factor table is a bonus worth as
much as the primes: dividing a number by its smallest prime factor
repeatedly factorizes it in time proportional to the number of
prime factors, no trial division. This module returns the primes
and the factor table, and tests check the prime counts against the
known values of the prime-counting function and confirm the factor
table reconstructs each number, so both outputs are verified.
"""

from __future__ import annotations

from rill.errors import Invalid


def linear_sieve(limit: int) -> tuple[list[int], list[int]]:
    if limit < 0:
        raise Invalid("limit must not be negative")
    smallest = [0] * (limit + 1)
    primes: list[int] = []
    for i in range(2, limit + 1):
        if smallest[i] == 0:
            smallest[i] = i
            primes.append(i)
        for p in primes:
            if p > smallest[i] or i * p > limit:
                break
            smallest[i * p] = p
    return primes, smallest


def factorize(n: int, smallest: list[int]) -> list[int]:
    if n < 1:
        raise Invalid("n must be at least 1")
    if n >= len(smallest):
        raise Invalid("n is beyond the sieved range")
    factors: list[int] = []
    while n > 1:
        p = smallest[n]
        factors.append(p)
        n //= p
    return factors

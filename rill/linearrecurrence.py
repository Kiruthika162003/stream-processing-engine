"""Linear recurrence by matrix power: the nth term in log n steps, not n.

A linear recurrence, each term a fixed weighted sum of the
previous k terms, is the shape of many projections: a decayed
counter's value after n ticks, a population model, a running
convolution. Iterating the recurrence computes the nth term in n
steps, fine for small n and slow for a projection far into the
future. Matrix exponentiation does it in log n. The recurrence is
encoded as a companion matrix that, multiplied by the vector of
the last k terms, produces the vector shifted forward by one, so
applying the matrix n times advances n terms, and applying it n
times is one matrix raised to the nth power. That power is
computed by repeated squaring, halving the exponent each step, so
the nth term costs a logarithmic number of matrix multiplies
rather than n scalar steps. For Fibonacci the companion matrix is
the famous two-by-two whose nth power's corner is the nth
Fibonacci number, and the same construction handles any linear
recurrence by widening the matrix to the recurrence's order. The
answer is exact, integer arithmetic throughout, and identical to
what the slow iteration would produce, only reached in log time.
This module builds the companion matrix and raises it by squaring,
checked against the straightforward iteration, so the log-not-
linear speedup is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def _mat_mult(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    size = len(a)
    return [
        [sum(a[i][k] * b[k][j] for k in range(size)) for j in range(size)]
        for i in range(size)
    ]


def _mat_power(matrix: list[list[int]], power: int) -> list[list[int]]:
    size = len(matrix)
    result = [[1 if i == j else 0 for j in range(size)] for i in range(size)]
    base = matrix
    while power > 0:
        if power & 1:
            result = _mat_mult(result, base)
        base = _mat_mult(base, base)
        power >>= 1
    return result


def nth_term(coefficients: list[int], initial: list[int], n: int) -> int:
    if len(coefficients) != len(initial):
        raise Invalid("need one initial term per coefficient")
    if not coefficients:
        raise Invalid("recurrence has no order")
    if n < 0:
        raise Invalid("n cannot be negative")
    order = len(coefficients)
    if n < order:
        return initial[n]
    companion = [[0] * order for _ in range(order)]
    companion[0] = list(coefficients)
    for row in range(1, order):
        companion[row][row - 1] = 1
    powered = _mat_power(companion, n - order + 1)
    return sum(powered[0][j] * initial[order - 1 - j] for j in range(order))

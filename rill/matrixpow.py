"""Matrix power by repeated squaring: the nth term of a linear recurrence in log n.

A linear recurrence, where each term is a fixed linear combination
of the previous few, can be advanced one step by multiplying a
state vector by a fixed transition matrix. Advancing n steps is
that matrix raised to the n, and the naive way, multiplying it in n
times, is linear in n. Repeated squaring does it in log n matrix
multiplications instead: to raise M to the n, look at n in binary,
square M repeatedly to get M, M squared, M to the fourth, and so
on, and multiply together the powers whose bits are set. Since n
has log n bits, log n squarings and at most log n multiplies
suffice. The classic case is Fibonacci: the two-by-two matrix
[[1,1],[1,0]] raised to the n has the nth Fibonacci number in its
corner, so the nth Fibonacci comes out in log n matrix multiplies
rather than n additions, which matters when n is astronomically
large. The technique generalizes to any linear recurrence by
writing its transition matrix, and the same log-n cost applies. The
identity matrix is the right starting accumulator, the multiplicative
one, just as one is for ordinary powers. This module multiplies and
powers square matrices and exposes an nth-Fibonacci built on the
matrix, and a test checks the matrix Fibonacci against the plain
iterative one across a range, so the log-n route is confirmed to
agree with the linear one.
"""

from __future__ import annotations

from rill.errors import Invalid

Matrix = list[list[int]]


def _identity(n: int) -> Matrix:
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def multiply(a: Matrix, b: Matrix) -> Matrix:
    if a is None or b is None:
        raise Invalid("matrices must not be None")
    if len(a[0]) != len(b):
        raise Invalid("inner dimensions must match to multiply")
    rows, inner, cols = len(a), len(b), len(b[0])
    out = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        arow = a[i]
        for k in range(inner):
            aik = arow[k]
            if aik:
                brow = b[k]
                orow = out[i]
                for j in range(cols):
                    orow[j] += aik * brow[j]
    return out


def matrix_power(matrix: Matrix, exponent: int) -> Matrix:
    if matrix is None:
        raise Invalid("matrix must not be None")
    if exponent < 0:
        raise Invalid("exponent must not be negative")
    if len(matrix) != len(matrix[0]):
        raise Invalid("matrix must be square")
    result = _identity(len(matrix))
    base = [row[:] for row in matrix]
    while exponent > 0:
        if exponent & 1:
            result = multiply(result, base)
        base = multiply(base, base)
        exponent >>= 1
    return result


def fibonacci(n: int) -> int:
    if n < 0:
        raise Invalid("n must not be negative")
    if n == 0:
        return 0
    return matrix_power([[1, 1], [1, 0]], n)[0][1]

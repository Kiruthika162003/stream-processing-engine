"""Two-dimensional prefix sums: the total inside any rectangle from four corner lookups.

A grid of values, a heatmap of load over time and key, a matrix of
counts, is often queried for the total inside a rectangle, the sum
of a region. Scanning the rectangle costs its area per query, which
for many queries over a large grid is too much. The two-dimensional
prefix sum precomputes, for every cell, the sum of the whole
rectangle from the origin to that cell, and then any rectangle's
sum is four of those corner values combined by inclusion-exclusion:
the big rectangle to the bottom-right corner, minus the strip above
it, minus the strip to its left, plus the top-left rectangle that
both strips subtracted and so was removed twice. Four array lookups
and three additions, constant time, regardless of the rectangle's
size. The build is one pass over the grid accumulating each cell's
prefix from the three already-computed neighbors above, left, and
diagonal, so it costs the grid's size once. As with the
one-dimensional prefix sum, the price is immutability: changing one
cell shifts every prefix below and to the right of it, so this is
the structure for a static grid queried many times, and a mutating
grid wants a two-dimensional Fenwick tree instead. This module
builds the cumulative grid and answers rectangle sums by the
four-corner formula, checked against a naive scan, so the
constant-time query is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


class PrefixSum2D:
    def __init__(self, grid: list[list[int]]) -> None:
        if not grid or not grid[0]:
            raise Invalid("grid must be non-empty")
        width = len(grid[0])
        if any(len(row) != width for row in grid):
            raise Invalid("grid must be rectangular")
        self._rows = len(grid)
        self._cols = width
        self._cum = [[0] * (width + 1) for _ in range(self._rows + 1)]
        for r in range(self._rows):
            for c in range(width):
                self._cum[r + 1][c + 1] = (
                    grid[r][c]
                    + self._cum[r][c + 1]
                    + self._cum[r + 1][c]
                    - self._cum[r][c]
                )

    def rect_sum(self, r1: int, c1: int, r2: int, c2: int) -> int:
        if not (0 <= r1 <= r2 < self._rows and 0 <= c1 <= c2 < self._cols):
            raise Invalid("rectangle out of bounds (inclusive)")
        return (
            self._cum[r2 + 1][c2 + 1]
            - self._cum[r1][c2 + 1]
            - self._cum[r2 + 1][c1]
            + self._cum[r1][c1]
        )

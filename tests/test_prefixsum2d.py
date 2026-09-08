from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.prefixsum2d import PrefixSum2D


class TestRectSum:
    def test_a_concrete_rectangle(self):
        grid = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        ps = PrefixSum2D(grid)
        assert ps.rect_sum(0, 0, 1, 1) == 1 + 2 + 4 + 5
        assert ps.rect_sum(1, 1, 2, 2) == 5 + 6 + 8 + 9

    def test_the_full_grid_is_the_total(self):
        grid = [[1, 2], [3, 4]]
        assert PrefixSum2D(grid).rect_sum(0, 0, 1, 1) == 10

    def test_a_single_cell(self):
        grid = [[1, 2], [3, 4]]
        assert PrefixSum2D(grid).rect_sum(1, 0, 1, 0) == 3

    def test_it_matches_a_naive_scan(self):
        rng = random.Random(5)
        for _ in range(300):
            rows, cols = rng.randint(1, 8), rng.randint(1, 8)
            grid = [[rng.randint(-5, 5) for _ in range(cols)] for _ in range(rows)]
            ps = PrefixSum2D(grid)
            for _ in range(10):
                r1 = rng.randrange(rows)
                r2 = rng.randint(r1, rows - 1)
                c1 = rng.randrange(cols)
                c2 = rng.randint(c1, cols - 1)
                expected = sum(
                    grid[r][c]
                    for r in range(r1, r2 + 1)
                    for c in range(c1, c2 + 1)
                )
                assert ps.rect_sum(r1, c1, r2, c2) == expected


class TestRefusals:
    def test_an_empty_grid_is_refused(self):
        with pytest.raises(Invalid):
            PrefixSum2D([])

    def test_a_ragged_grid_is_refused(self):
        with pytest.raises(Invalid):
            PrefixSum2D([[1, 2], [3]])

    def test_an_out_of_bounds_rectangle_is_refused(self):
        with pytest.raises(Invalid):
            PrefixSum2D([[1, 2], [3, 4]]).rect_sum(0, 0, 5, 5)

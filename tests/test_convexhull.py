from __future__ import annotations

import random

import pytest

from rill.convexhull import _cross, convex_hull
from rill.errors import Invalid


def _inside_or_on(hull: list[tuple[float, float]], p: tuple[float, float]) -> bool:
    n = len(hull)
    if n < 3:
        return True
    return all(_cross(hull[i], hull[(i + 1) % n], p) >= -1e-9 for i in range(n))


class TestHull:
    def test_a_square_drops_its_interior_points(self):
        pts = [(0, 0), (4, 0), (4, 4), (0, 4), (2, 2), (1, 1), (3, 1)]
        assert convex_hull(pts) == [(0, 0), (4, 0), (4, 4), (0, 4)]

    def test_collinear_points_collapse_to_the_endpoints(self):
        assert convex_hull([(0, 0), (1, 1), (2, 2), (3, 3)]) == [(0, 0), (3, 3)]

    def test_the_hull_encloses_every_input_point(self):
        rng = random.Random(17)
        for _ in range(3000):
            pts = [
                (rng.randint(-20, 20), rng.randint(-20, 20))
                for _ in range(rng.randint(1, 30))
            ]
            hull = convex_hull(pts)
            assert all(_inside_or_on(hull, p) for p in pts)


class TestEdges:
    def test_few_points_are_returned_as_is(self):
        assert convex_hull([]) == []
        assert convex_hull([(1, 1)]) == [(1, 1)]
        assert convex_hull([(1, 1), (2, 2)]) == [(1, 1), (2, 2)]

    def test_duplicate_points_are_deduplicated(self):
        assert convex_hull([(0, 0), (0, 0), (2, 2)]) == [(0, 0), (2, 2)]


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            convex_hull(None)

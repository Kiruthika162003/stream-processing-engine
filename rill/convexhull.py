"""Convex hull by monotone chain: the tightest polygon enclosing a set of points.

The convex hull of a set of points is the smallest convex polygon
that contains them all, the shape a rubber band would take if
stretched around the outermost points and released. Andrew's
monotone chain builds it in n log n, dominated by one sort of the
points by x then y. After sorting it sweeps left to right building
the lower boundary and right to left building the upper one, and
the two chains joined make the full hull. The engine of both sweeps
is a turn test on the last three points via the cross product of
the two edges between them. A positive cross means a
counterclockwise, left, turn; zero means the three are collinear;
negative means a clockwise, right, turn. While adding a point would
make the chain turn the wrong way, the middle point is popped,
because it lies inside the turn and cannot be a hull vertex. Each
point is pushed and popped at most once per chain, so the sweep
itself is linear and the sort is the only n-log-n cost. Two choices
worth stating because they are easy to get wrong: using a strict
inequality on the cross product keeps collinear points off the hull
edges, which is usually what is wanted, and the first point of each
chain is dropped when concatenating so the two shared endpoints are
not counted twice. This module returns the hull in counterclockwise
order starting from the lowest-leftmost point, and a test checks
that every input point lies inside or on the returned hull, so the
polygon genuinely encloses the set.
"""

from __future__ import annotations

from rill.errors import Invalid


def _cross(o: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if points is None:
        raise Invalid("points must not be None")
    unique = sorted(set(points))
    if len(unique) <= 2:
        return unique
    lower: list[tuple[float, float]] = []
    for p in unique:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[float, float]] = []
    for p in reversed(unique):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]

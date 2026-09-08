"""Simpson's rule: integrate by fitting parabolas, exact through cubics.

Approximating a definite integral by summing rectangles or trapezoids
fits the function with flat or straight pieces, and the error shrinks
only linearly or quadratically as the pieces narrow. Simpson's rule
fits parabolas instead, one through each consecutive triple of sample
points, and integrates those exactly. The composite rule samples the
interval at an even number of equal steps and weights the samples in
the pattern one, four, two, four, two, and so on to four, one, times
the step over three: the endpoints once, the odd-indexed interior
points four times, the even-indexed interior points twice. The
striking property, more than the parabola fit alone would suggest, is
that Simpson's rule is exact not just for quadratics but for cubics
too. The cubic term's error over each symmetric pair of panels
cancels itself, so a rule built to be exact for degree two comes out
exact for degree three for free, and its error scales with the fourth
power of the step, dropping by sixteen each time the step is halved,
far faster than the trapezoid rule's fourfold. The requirement is an
even number of intervals, since the parabolas are fitted over pairs
of panels, and a rule given an odd count cannot pair them, so the
honest response is to refuse rather than silently mishandle the last
panel. The finding worth stating is the free extra degree: exact
through cubics from a quadratic construction, which is why Simpson is
the default low-order quadrature. This module integrates by composite
Simpson, and a test checks it is exact on cubic polynomials and
converges at the fourth-power rate on a transcendental function, so
both claims are confirmed.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


def integrate(
    func: Callable[[float], float], low: float, high: float, intervals: int
) -> float:
    if func is None:
        raise Invalid("a function is required")
    if intervals <= 0 or intervals % 2 != 0:
        raise Invalid("intervals must be a positive even number")
    if high < low:
        raise Invalid("high must not be below low")
    if high == low:
        return 0.0
    step = (high - low) / intervals
    total = func(low) + func(high)
    for i in range(1, intervals):
        weight = 4 if i % 2 == 1 else 2
        total += weight * func(low + i * step)
    return total * step / 3

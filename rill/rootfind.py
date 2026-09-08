"""Root finding: bisection always converges slowly, Newton converges fast or not at all.

Solving f(x) equals zero, inverting a latency-versus-load curve to
find the load that hits a target, sizing a parameter to meet a
budget, comes down to root finding, and the two classic methods
trade robustness against speed in opposite directions. Bisection
brackets a root between two points where the function has opposite
signs and repeatedly halves the interval, keeping the half that
still straddles zero. It cannot fail once a sign change is
bracketed, but it is slow: each step buys exactly one more bit of
the answer, so reaching a small tolerance takes a number of steps
proportional to the digits wanted. Newton's method uses the
derivative to jump from the current guess to where the tangent
line crosses zero, which near a root doubles the number of correct
digits each step, converging in a handful of iterations, but it
needs the derivative, and a poor starting guess or a flat spot can
send it diverging away from the root entirely with no bracket to
save it. So bisection is the method you trust and Newton is the
method you race, and a robust solver often brackets with bisection
and then switches to Newton once close. This module runs both and
counts the iterations, so the linear-versus-quadratic convergence
is a measured gap on the same equation.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


def bisect_root(
    f: Callable[[float], float], lo: float, hi: float, tolerance: float = 1e-10
) -> tuple[float, int]:
    if tolerance <= 0:
        raise Invalid("tolerance must be positive")
    if f(lo) * f(hi) > 0:
        raise Invalid("f must change sign across [lo, hi]")
    iterations = 0
    while hi - lo > tolerance:
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
        iterations += 1
    return (lo + hi) / 2, iterations


def newton_root(
    f: Callable[[float], float],
    df: Callable[[float], float],
    start: float,
    tolerance: float = 1e-10,
    max_iterations: int = 100,
) -> tuple[float, int]:
    if tolerance <= 0:
        raise Invalid("tolerance must be positive")
    x = start
    for iterations in range(1, max_iterations + 1):
        slope = df(x)
        if slope == 0:
            raise Invalid("derivative is zero; Newton cannot step")
        nxt = x - f(x) / slope
        if abs(nxt - x) < tolerance:
            return nxt, iterations
        x = nxt
    raise Invalid("Newton did not converge within the iteration budget")

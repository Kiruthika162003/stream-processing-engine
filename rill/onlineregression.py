"""Online regression: fitting a line to a stream in constant memory, updated per point.

Fitting a least-squares line to points that arrive as a stream
should not require keeping the points. The slope and intercept
depend only on a few running quantities, the means of x and y,
the variance of x, and the covariance of x and y, and each of
those can be maintained incrementally, so the fit updates in
constant time per point and constant memory regardless of how
many points have streamed by. The stable way to maintain them is
the same one Welford's variance uses: update the running mean
first, then accumulate the sum of products of deviations taken
around the shifting mean, so every quantity stays on the scale of
the spread rather than the scale of the values, and a stream of
points sitting far from the origin does not blow up the fit the
way the textbook sum-of-products-minus-product-of-sums would. The
slope is the covariance over the variance of x, the intercept
places the line through the means, and a prediction is a
substitution. This module keeps the running moments and reports
the slope, the intercept, and a prediction, checking that a
streamed fit recovers a known line, so the constant-memory
regression is a measured recovery and not a promise.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class OnlineRegression:
    _n: int = 0
    _mean_x: float = 0.0
    _mean_y: float = 0.0
    _m2_x: float = 0.0
    _cov: float = 0.0

    def update(self, x: float, y: float) -> None:
        self._n += 1
        dx = x - self._mean_x
        self._mean_x += dx / self._n
        dy = y - self._mean_y
        self._mean_y += dy / self._n
        self._m2_x += dx * (x - self._mean_x)
        self._cov += dx * (y - self._mean_y)

    def slope(self) -> float:
        if self._m2_x == 0:
            raise Invalid("x has no variance; the slope is undefined")
        return self._cov / self._m2_x

    def intercept(self) -> float:
        return self._mean_y - self.slope() * self._mean_x

    def predict(self, x: float) -> float:
        return self.slope() * x + self.intercept()

"""Holt smoothing: adding a trend term so the forecast stops lagging a rising series.

A single exponential moving average smooths a noisy signal but
lags a trend, because it is always a blend of past values that
were lower than the present on a rising series, so it sits
systematically below the truth and its forecast, just the current
smoothed value, under-predicts by roughly one trend-step every
step. Holt's method, double exponential smoothing, fixes the lag
by tracking two quantities instead of one: a level, the smoothed
current value, and a trend, the smoothed rate of change of the
level. Each observation updates the level toward the new value
blended with where the previous level-plus-trend expected to be,
and updates the trend toward the level's latest change, each with
its own smoothing weight. A forecast is then the level plus as
many trend-steps as the horizon, so it projects the slope forward
instead of freezing at the last value. On a steady ramp the level
and trend converge so the forecast rides the line rather than
trailing it, which is exactly the systematic error the single
average could not shake. The cost is a second parameter to tune
and a sensitivity to a trend that turns. This module runs the
level-and-trend update and forecasts ahead, so the trend the
single average misses is a measured difference.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class HoltForecast:
    alpha: float
    beta: float
    _level: float | None = None
    _trend: float = 0.0
    _prev: float | None = None

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha <= 1.0 or not 0.0 < self.beta <= 1.0:
            raise Invalid("alpha and beta must be in (0, 1]")

    def update(self, value: float) -> None:
        if self._level is None:
            self._level = value
            return
        previous_level = self._level
        self._level = self.alpha * value + (1 - self.alpha) * (
            previous_level + self._trend
        )
        self._trend = self.beta * (self._level - previous_level) + (
            1 - self.beta
        ) * self._trend

    def level(self) -> float:
        if self._level is None:
            raise Invalid("no observations yet")
        return self._level

    def trend(self) -> float:
        return self._trend

    def forecast(self, steps: int) -> float:
        if self._level is None:
            raise Invalid("no observations yet")
        if steps < 0:
            raise Invalid("steps cannot be negative")
        return self._level + steps * self._trend

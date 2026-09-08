from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.ewma import Ewma
from rill.holtsmoothing import HoltForecast


def _ramp_holt() -> HoltForecast:
    holt = HoltForecast(alpha=0.5, beta=0.3)
    for step in range(1, 51):
        holt.update(10 * step)
    return holt


class TestTrackingATrend:
    def test_holt_learns_the_level_and_the_slope(self):
        holt = _ramp_holt()
        assert round(holt.level(), 1) == 500.0
        assert round(holt.trend(), 1) == 10.0

    def test_the_forecast_projects_the_slope_forward(self):
        holt = _ramp_holt()
        assert round(holt.forecast(1), 1) == 510.0  # the next actual

    def test_single_exponential_smoothing_lags_the_trend(self):
        ewma = Ewma(alpha=0.5)
        for step in range(1, 51):
            ewma.update(10 * step)
        # the single average sits below the current actual of 500
        assert ewma.raw() < 500


class TestFlat:
    def test_a_flat_series_has_no_trend(self):
        holt = HoltForecast(alpha=0.5, beta=0.3)
        for _ in range(30):
            holt.update(100)
        assert abs(holt.trend()) < 1e-6
        assert round(holt.forecast(5), 1) == 100.0


class TestRefusals:
    def test_alpha_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            HoltForecast(alpha=0, beta=0.5)

    def test_a_forecast_before_observations_is_refused(self):
        with pytest.raises(Invalid):
            HoltForecast(alpha=0.5, beta=0.5).forecast(1)

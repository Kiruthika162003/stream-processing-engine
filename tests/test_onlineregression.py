from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.onlineregression import OnlineRegression


class TestRecovery:
    def test_it_recovers_a_known_line(self):
        reg = OnlineRegression()
        for x in range(100):
            reg.update(x, 2 * x + 3)
        assert round(reg.slope(), 6) == 2.0
        assert round(reg.intercept(), 6) == 3.0

    def test_prediction_extrapolates_the_line(self):
        reg = OnlineRegression()
        for x in range(100):
            reg.update(x, 2 * x + 3)
        assert round(reg.predict(1000), 4) == 2003.0

    def test_it_is_stable_on_large_offset_inputs(self):
        reg = OnlineRegression()
        for x in range(100):
            reg.update(1e9 + x, 2 * (1e9 + x) + 3)
        assert round(reg.slope(), 6) == 2.0


class TestRefusals:
    def test_a_vertical_cloud_has_no_slope(self):
        reg = OnlineRegression()
        for _ in range(5):
            reg.update(7, 1)  # all the same x
        with pytest.raises(Invalid):
            reg.slope()

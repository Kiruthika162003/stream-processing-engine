from __future__ import annotations

import pytest

from rill.checkpointinterval import optimal_interval, waste_rate
from rill.errors import Invalid

COST, MTBF = 10, 5000


class TestOptimum:
    def test_the_optimal_interval_is_youngs_formula(self):
        assert round(optimal_interval(COST, MTBF), 2) == 316.23

    def test_the_optimum_minimizes_the_waste(self):
        opt = optimal_interval(COST, MTBF)
        at_opt = waste_rate(opt, COST, MTBF)
        assert at_opt < waste_rate(opt / 2, COST, MTBF)
        assert at_opt < waste_rate(opt * 2, COST, MTBF)

    def test_the_waste_is_symmetric_around_the_optimum(self):
        opt = optimal_interval(COST, MTBF)
        assert round(waste_rate(opt / 2, COST, MTBF), 5) == round(
            waste_rate(opt * 2, COST, MTBF), 5
        )


class TestRefusals:
    def test_a_nonpositive_interval_is_refused(self):
        with pytest.raises(Invalid):
            waste_rate(0, COST, MTBF)

    def test_a_nonpositive_cost_is_refused(self):
        with pytest.raises(Invalid):
            optimal_interval(0, MTBF)

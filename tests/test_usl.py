from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.usl import peak_workers, throughput

CONTENTION, COHERENCY = 0.03, 0.001


class TestRetrograde:
    def test_the_peak_is_where_the_law_predicts(self):
        assert round(peak_workers(CONTENTION, COHERENCY), 1) == 31.1

    def test_throughput_rises_to_the_peak_then_falls(self):
        at_peak = throughput(31, CONTENTION, COHERENCY)
        assert at_peak > throughput(16, CONTENTION, COHERENCY)
        assert at_peak > throughput(64, CONTENTION, COHERENCY)

    def test_more_workers_past_the_peak_are_slower(self):
        assert throughput(100, CONTENTION, COHERENCY) < throughput(
            31, CONTENTION, COHERENCY
        )


class TestAmdahlLimit:
    def test_without_coherency_the_curve_never_declines(self):
        # beta = 0 is Amdahl: it plateaus but keeps rising toward 1/alpha
        assert throughput(1000, 0.03, 0) > throughput(100, 0.03, 0)

    def test_the_peak_needs_a_coherency_term(self):
        with pytest.raises(Invalid):
            peak_workers(0.03, 0)


class TestRefusals:
    def test_zero_workers_is_refused(self):
        with pytest.raises(Invalid):
            throughput(0, CONTENTION, COHERENCY)

    def test_a_negative_coefficient_is_refused(self):
        with pytest.raises(Invalid):
            throughput(10, -0.1, COHERENCY)

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.quantile import QuantileSummary


def uniform_summary(budget: int = 50) -> QuantileSummary:
    summary = QuantileSummary(budget=budget)
    for value in range(1, 1001):
        summary.observe(value)
    return summary


class TestAccuracy:
    def test_the_median_tracks_truth_within_the_error(self):
        summary = uniform_summary()
        assert abs(summary.quantile(0.5) - 500) <= 30

    def test_the_tail_tracks_truth_within_the_error(self):
        summary = uniform_summary()
        assert abs(summary.quantile(0.9) - 900) <= 30
        assert abs(summary.quantile(0.99) - 990) <= 30

    def test_the_summary_stays_within_budget(self):
        summary = uniform_summary(budget=50)
        assert len(summary.samples) <= 50

    def test_a_tiny_budget_is_refused(self):
        with pytest.raises(Invalid):
            QuantileSummary(budget=3)


class TestTheAnswer:
    def test_the_answer_carries_its_rank_error(self):
        summary = uniform_summary()
        answer = summary.answer(0.99)
        assert answer.startswith("p99 ~=")
        assert "rank error at most" in answer
        assert "never quoted barer than it is known" in answer

    def test_ranks_are_fractions_in_the_unit_interval(self):
        summary = uniform_summary()
        with pytest.raises(Invalid):
            summary.quantile(0)
        with pytest.raises(Invalid):
            summary.quantile(1.5)

    def test_an_empty_summary_has_no_quantile(self):
        with pytest.raises(Invalid):
            QuantileSummary(budget=8).quantile(0.5)

    def test_a_smaller_budget_yields_a_larger_error(self):
        tight = uniform_summary(budget=10)
        loose = uniform_summary(budget=100)
        assert tight._rank_error() > loose._rank_error()

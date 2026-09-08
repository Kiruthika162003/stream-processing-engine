from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.hyperloglog import CardinalityEstimator


class TestEstimation:
    def test_the_estimate_is_within_its_band(self):
        estimator = CardinalityEstimator()
        for number in range(1000):
            estimator.observe(f"user-{number}")
        estimate = estimator.estimate()
        assert 850 < estimate < 1150

    def test_repeated_values_do_not_inflate_the_count(self):
        estimator = CardinalityEstimator()
        for _ in range(1000):
            estimator.observe("the-same-user")
        assert estimator.estimate() < 5

    def test_the_report_carries_its_error_band(self):
        estimator = CardinalityEstimator()
        for number in range(100):
            estimator.observe(f"u-{number}")
        report = estimator.report(error_percent=5)
        assert "distinct (+/-" in report
        assert "will never match" in report


class TestMerge:
    def test_two_shards_merge_into_the_union(self):
        left = CardinalityEstimator()
        right = CardinalityEstimator()
        for number in range(500):
            left.observe(f"x-{number}")
        for number in range(250, 750):
            right.observe(f"x-{number}")
        merged = left.merge(right)
        assert 650 < merged.estimate() < 850

    def test_the_merge_does_not_mutate_the_inputs(self):
        left = CardinalityEstimator()
        left.observe("a")
        before = list(left.registers)
        right = CardinalityEstimator()
        right.observe("b")
        left.merge(right)
        assert left.registers == before

    def test_mismatched_widths_cannot_merge(self):
        left = CardinalityEstimator()
        right = CardinalityEstimator(registers=[0, 0])
        with pytest.raises(Invalid):
            left.merge(right)

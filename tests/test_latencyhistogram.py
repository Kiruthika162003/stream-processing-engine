from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.latencyhistogram import LatencyHistogram


def skewed() -> LatencyHistogram:
    histogram = LatencyHistogram()
    for _ in range(980):
        histogram.observe(5)
    for _ in range(20):
        histogram.observe(5000)
    return histogram


class TestPercentiles:
    def test_the_median_sits_in_the_fast_bucket(self):
        assert skewed().percentile(50) == 10

    def test_the_p99_finds_the_tail_the_mean_hides(self):
        histogram = skewed()
        assert histogram.percentile(99) == 10000
        assert histogram.mean() < 200

    def test_a_bad_percentile_is_refused(self):
        with pytest.raises(Invalid):
            skewed().percentile(0)

    def test_negative_latency_is_refused(self):
        with pytest.raises(Invalid):
            LatencyHistogram().observe(-1)


class TestTheReport:
    def test_the_report_pairs_mean_with_the_tail(self):
        report = skewed().report()
        assert "p50 10" in report
        assert "p99 10000" in report
        assert "fails the slowest one percent" in report

    def test_an_empty_histogram_has_no_report(self):
        with pytest.raises(Invalid):
            LatencyHistogram().mean()

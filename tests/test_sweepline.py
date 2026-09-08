from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.sweepline import all_overlaps, peak_concurrency


class TestPeak:
    def test_overlapping_intervals_peak_at_the_common_instant(self):
        peak, when = peak_concurrency([(0, 10), (5, 15), (8, 12)])
        assert peak == 3
        assert when == 8

    def test_half_open_touching_intervals_do_not_overlap(self):
        peak, _ = peak_concurrency([(0, 5), (5, 10)])
        assert peak == 1

    def test_a_staircase_peaks_where_the_most_are_live(self):
        peak, when = peak_concurrency([(0, 4), (1, 5), (2, 6), (10, 12)])
        assert peak == 3
        assert when == 2


class TestStabbing:
    def test_all_overlaps_returns_the_intervals_covering_a_point(self):
        intervals = [(0, 10), (5, 15), (8, 12), (20, 25)]
        assert all_overlaps(intervals, 9) == [(0, 10), (5, 15), (8, 12)]

    def test_the_right_endpoint_is_excluded(self):
        assert all_overlaps([(0, 5)], 5) == []


class TestRefusals:
    def test_no_intervals_is_refused(self):
        with pytest.raises(Invalid):
            peak_concurrency([])

    def test_an_inverted_interval_is_refused(self):
        with pytest.raises(Invalid):
            peak_concurrency([(10, 5)])

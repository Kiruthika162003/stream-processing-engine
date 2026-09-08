from __future__ import annotations

import pytest

from rill.coordinatedomission import correct, percentile
from rill.errors import Invalid

MEASURED = [1] * 990 + [500] + [1] * 9


class TestHiddenTail:
    def test_the_naive_p99_hides_the_stall(self):
        assert percentile(MEASURED, 0.99) == 1

    def test_the_correction_backfills_the_omitted_requests(self):
        corrected = correct(MEASURED, expected_interval=1)
        assert len(corrected) == 1499  # 1000 measured + 499 backfilled

    def test_the_corrected_p99_reveals_the_stall(self):
        corrected = correct(MEASURED, expected_interval=1)
        assert percentile(corrected, 0.99) == 485

    def test_the_median_is_untouched_by_the_correction(self):
        corrected = correct(MEASURED, expected_interval=1)
        assert percentile(MEASURED, 0.5) == 1
        assert percentile(corrected, 0.5) == 1


class TestNoStall:
    def test_latencies_within_the_interval_are_left_alone(self):
        measured = [1, 1, 1]
        assert correct(measured, expected_interval=1) == [1, 1, 1]


class TestRefusals:
    def test_a_nonpositive_interval_is_refused(self):
        with pytest.raises(Invalid):
            correct([1], expected_interval=0)

    def test_a_bad_quantile_is_refused(self):
        with pytest.raises(Invalid):
            percentile([1], 1.5)

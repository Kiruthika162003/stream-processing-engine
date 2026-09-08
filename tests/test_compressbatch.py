from __future__ import annotations

import pytest

from rill.compressbatch import CompressionModel
from rill.errors import Invalid


def model() -> CompressionModel:
    return CompressionModel()


class TestTheCurve:
    def test_a_single_event_compresses_barely(self):
        assert model().ratio(1) == pytest.approx(0.71, abs=0.01)

    def test_ten_similar_events_share_their_redundancy(self):
        assert model().ratio(10) == pytest.approx(1.38, abs=0.01)

    def test_the_hundredth_event_buys_most_of_the_rest(self):
        assert model().ratio(100) == pytest.approx(2.92, abs=0.01)

    def test_the_thousandth_buys_almost_nothing(self):
        gain = model().ratio(1000) - model().ratio(100)
        assert gain < 0.4

    def test_an_empty_batch_is_refused(self):
        with pytest.raises(Invalid):
            model().compressed_size(0)


class TestTheTable:
    def test_the_elbows_are_on_display(self):
        table = model().elbow_table([1, 10, 100, 1000])
        assert "batch 10: ratio 1.38 (+0.67)" in table
        assert "batch 1000: ratio 3.29 (+0.37)" in table
        assert "retry weight 30425 byte(s)" in table
        assert "just-batch-more" in table

    def test_one_point_makes_no_elbow(self):
        with pytest.raises(Invalid):
            model().elbow_table([10])

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.retraction import RetractableMax, RetractableSum


class TestRetractableSum:
    def test_a_retraction_subtracts_in_constant_time(self):
        agg = RetractableSum()
        for value in (10, 20, 30):
            agg.insert(value)
        agg.retract(20)
        assert agg.total() == 40

    def test_retracting_from_nothing_is_refused(self):
        with pytest.raises(Invalid):
            RetractableSum().retract(5)


class TestRetractableMax:
    def test_retracting_a_non_max_leaves_the_max(self):
        agg = RetractableMax()
        for value in (10, 50, 30):
            agg.insert(value)
        agg.retract(10)
        assert agg.maximum() == 50
        assert agg.recomputes() == 0

    def test_retracting_the_max_forces_a_recompute(self):
        agg = RetractableMax()
        for value in (10, 50, 30):
            agg.insert(value)
        agg.retract(50)
        assert agg.maximum() == 30  # had to look at what remained
        assert agg.recomputes() == 1

    def test_duplicates_are_kept_in_the_multiset(self):
        agg = RetractableMax()
        agg.insert(50)
        agg.insert(50)
        agg.retract(50)
        assert agg.maximum() == 50  # one 50 remains

    def test_retracting_an_absent_value_is_refused(self):
        agg = RetractableMax()
        agg.insert(1)
        with pytest.raises(Invalid):
            agg.retract(9)

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.intervaljoin import interval_join

ORDERS = [("o1", 100), ("o2", 200)]
PAYMENTS = [("o1", 150), ("o2", 180)]  # o2 payment precedes its order


class TestCausalBound:
    def test_a_forward_bound_excludes_the_backward_match(self):
        # payment must follow its order, within [0, 300]
        assert interval_join(ORDERS, PAYMENTS, 0, 300) == [("o1", 100, 150)]

    def test_a_symmetric_bound_wrongly_admits_the_backward_match(self):
        assert interval_join(ORDERS, PAYMENTS, -300, 300) == [
            ("o1", 100, 150),
            ("o2", 200, 180),
        ]


class TestBoundaries:
    def test_the_window_is_inclusive_at_both_ends(self):
        left = [("k", 0)]
        right = [("k", 0), ("k", 5)]
        assert interval_join(left, right, 0, 5) == [("k", 0, 0), ("k", 0, 5)]

    def test_events_outside_the_window_do_not_match(self):
        left = [("k", 0)]
        right = [("k", 6)]
        assert interval_join(left, right, 0, 5) == []

    def test_different_keys_never_match(self):
        assert interval_join([("a", 0)], [("b", 1)], 0, 5) == []


class TestRefusals:
    def test_lower_above_upper_is_refused(self):
        with pytest.raises(Invalid):
            interval_join([], [], 5, 1)

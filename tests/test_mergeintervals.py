from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.mergeintervals import merge_intervals


class TestMerge:
    def test_overlapping_intervals_coalesce(self):
        result = merge_intervals([(1, 3), (2, 6), (8, 10), (15, 18)])
        assert result == [(1, 6), (8, 10), (15, 18)]

    def test_a_contained_interval_does_not_shrink_the_span(self):
        # the max-end rule keeps the containing span; a naive merge
        # taking the latest end would wrongly shrink it
        assert merge_intervals([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]

    def test_touching_intervals_merge_on_a_closed_boundary(self):
        assert merge_intervals([(1, 5), (5, 8)]) == [(1, 8)]

    def test_disjoint_intervals_are_unchanged(self):
        assert merge_intervals([(1, 2), (3, 4)]) == [(1, 2), (3, 4)]

    def test_unsorted_input_is_still_merged(self):
        assert merge_intervals([(8, 10), (1, 3), (2, 6)]) == [(1, 6), (8, 10)]


class TestEdges:
    def test_no_intervals_returns_empty(self):
        assert merge_intervals([]) == []

    def test_an_inverted_interval_is_refused(self):
        with pytest.raises(Invalid):
            merge_intervals([(5, 1)])

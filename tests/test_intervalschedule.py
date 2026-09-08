from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.intervalschedule import by_earliest_start, max_nonoverlapping


class TestOptimal:
    def test_earliest_finish_beats_the_earliest_start_heuristic(self):
        intervals = [(0, 10), (1, 3), (3, 5), (5, 7)]
        optimal = max_nonoverlapping(intervals)
        heuristic = by_earliest_start(intervals)
        assert optimal == [(1, 3), (3, 5), (5, 7)]
        assert len(optimal) == 3
        assert heuristic == [(0, 10)]
        assert len(heuristic) == 1

    def test_disjoint_intervals_are_all_selected(self):
        intervals = [(0, 1), (2, 3), (4, 5)]
        assert max_nonoverlapping(intervals) == intervals

    def test_touching_intervals_are_compatible(self):
        # half-open: [0,5) and [5,10) do not overlap
        assert max_nonoverlapping([(0, 5), (5, 10)]) == [(0, 5), (5, 10)]


class TestEdges:
    def test_no_intervals_selects_nothing(self):
        assert max_nonoverlapping([]) == []

    def test_an_inverted_interval_is_refused(self):
        with pytest.raises(Invalid):
            max_nonoverlapping([(5, 1)])

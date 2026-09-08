from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.hoppingwindow import HoppingWindows


class TestTheOverlap:
    def test_the_overlap_factor_is_size_over_hop(self):
        assert HoppingWindows(size=10, hop=5).overlap_factor() == 2
        assert HoppingWindows(size=10, hop=3).overlap_factor() == 4

    def test_an_event_falls_into_multiple_windows(self):
        windows = HoppingWindows(size=10, hop=5)
        assert windows.windows_for(25) == [20, 25]

    def test_early_events_do_not_reach_before_zero(self):
        windows = HoppingWindows(size=10, hop=5)
        assert windows.windows_for(3) == [0]

    def test_a_gappy_hop_is_refused(self):
        with pytest.raises(Invalid) as caught:
            HoppingWindows(size=5, hop=8)
        assert "fall through uncounted" in str(caught.value)


class TestCounting:
    def test_the_event_is_counted_in_each_window(self):
        windows = HoppingWindows(size=10, hop=5)
        verdict = windows.add(25)
        assert "counted in 2 window(s): [20, 25]" in verdict

    def test_the_inflation_is_correct_not_double_counting(self):
        windows = HoppingWindows(size=10, hop=5)
        for event_time in (22, 23, 24):
            windows.add(event_time)
        note = windows.inflation_note(events=3)
        assert "3 event(s) produced 6 window count(s)" in note
        assert "correct, not double-counting" in note
        assert "expecting it beats investigating it" in note

    def test_sizeless_windows_are_refused(self):
        with pytest.raises(Invalid):
            HoppingWindows(size=0, hop=1)

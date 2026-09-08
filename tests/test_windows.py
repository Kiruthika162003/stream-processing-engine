from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.windows import SessionTracker, Window, sliding, tumbling


class TestTheEdges:
    def test_windows_are_half_open_on_purpose(self):
        window = Window(start=10, end=20)
        assert window.holds(10)
        assert window.holds(19)
        assert not window.holds(20)

    def test_the_boundary_event_lands_in_exactly_one_tumble(self):
        left = tumbling(19, size=10)
        right = tumbling(20, size=10)
        assert left.label() == "[10, 20)"
        assert right.label() == "[20, 30)"
        assert not left.holds(20)

    def test_an_empty_window_contains_no_time(self):
        with pytest.raises(Invalid):
            Window(start=5, end=5)


class TestSliding:
    def test_one_event_belongs_to_several_windows(self):
        windows = sliding(25, size=10, slide=5)
        assert [w.label() for w in windows] == [
            "[20, 30)",
            "[25, 35)",
        ]
        assert all(w.holds(25) for w in windows)

    def test_early_events_do_not_reach_before_zero(self):
        windows = sliding(3, size=10, slide=5)
        assert [w.label() for w in windows] == ["[0, 10)"]

    def test_a_gappy_slide_is_refused(self):
        with pytest.raises(Invalid) as caught:
            sliding(10, size=5, slide=6)
        assert "fall into silently" in str(caught.value)


class TestSessions:
    def test_the_data_defines_the_window(self):
        tracker = SessionTracker(gap=5)
        assert tracker.observe(10) == "session opens at 10"
        assert "extends through 13" in tracker.observe(13)
        assert "extends through 13" in tracker.observe(12)

    def test_silence_closes_the_session_with_its_gap(self):
        tracker = SessionTracker(gap=5)
        tracker.observe(10)
        tracker.observe(13)
        verdict = tracker.observe(25)
        assert verdict.startswith(
            "silence outlasted the gap: [10, 18) closes"
        )
        assert "new session opens at 25" in verdict
        assert tracker.closed == [Window(start=10, end=18)]

    def test_a_zero_gap_is_refused(self):
        with pytest.raises(Invalid):
            SessionTracker(gap=0)

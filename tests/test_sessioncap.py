from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.sessioncap import CappedSessions


class TestGapClose:
    def test_an_idle_key_closes_on_the_gap(self):
        sessions = CappedSessions(gap=5, max_duration=100)
        sessions.event("k", 0)
        sessions.event("k", 1)
        assert sessions.event("k", 10) == (0, 1)

    def test_a_within_gap_event_extends_the_session(self):
        sessions = CappedSessions(gap=5, max_duration=100)
        sessions.event("k", 0)
        assert sessions.event("k", 2) is None


class TestCap:
    def test_an_uncapped_continuous_stream_never_closes(self):
        sessions = CappedSessions(gap=5, max_duration=10**9)
        closes = sum(
            1 for tick in range(250) if sessions.event("k", tick) is not None
        )
        assert closes == 0

    def test_the_cap_forces_a_close_on_a_relentless_key(self):
        sessions = CappedSessions(gap=5, max_duration=100)
        closes = sum(
            1 for tick in range(250) if sessions.event("k", tick) is not None
        )
        assert closes == 2


class TestRefusals:
    def test_a_nonpositive_setting_is_refused(self):
        with pytest.raises(Invalid):
            CappedSessions(gap=0, max_duration=100)

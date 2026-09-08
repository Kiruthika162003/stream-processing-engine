from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.globalwindow import GlobalWindow


class TestTheCountTrigger:
    def test_it_fires_every_threshold_events(self):
        window = GlobalWindow(
            trigger="count", count_threshold=3
        )
        assert window.add(1) is None
        assert window.add(1) is None
        verdict = window.add(1)
        assert "fired 3 and purged" in verdict

    def test_a_countless_count_trigger_is_refused(self):
        with pytest.raises(Invalid):
            GlobalWindow(trigger="count", count_threshold=0)

    def test_a_triggerless_window_is_a_memory_leak(self):
        with pytest.raises(Invalid) as caught:
            GlobalWindow(trigger="none")
        assert "a memory leak with a schema" in str(caught.value)


class TestTheTerminatorTrigger:
    def test_the_terminator_event_fires_the_window(self):
        window = GlobalWindow(trigger="terminator")
        window.add(5)
        window.add(3)
        verdict = window.add(0, is_terminator=True)
        assert "fired 8" in verdict


class TestPurgePolicy:
    def test_purge_on_fire_clears_the_state(self):
        window = GlobalWindow(
            trigger="count", count_threshold=2
        )
        window.add(5)
        window.add(5)
        assert window.total == 0
        assert "bounded memory between firings" in (
            window.memory_note()
        )

    def test_keep_on_fire_grows_forever(self):
        window = GlobalWindow(
            trigger="count",
            count_threshold=2,
            purge_on_fire=False,
        )
        window.add(5)
        verdict = window.add(5)
        assert "fired 10 and kept" in verdict
        assert window.total == 10
        assert "it grows forever" in window.memory_note()

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.sessionmerge import SessionMerger


def two_visits() -> SessionMerger:
    merger = SessionMerger(gap=5)
    merger.observe("user-1", 10)
    merger.observe("user-1", 12)
    merger.observe("user-1", 30)
    merger.observe("user-1", 33)
    return merger


class TestTheSpans:
    def test_separated_activity_makes_two_sessions(self):
        merger = two_visits()
        spans = merger.spans["user-1"]
        assert len(spans) == 2
        assert spans[0].label() == "[10, 12]"
        assert spans[1].label() == "[30, 33]"

    def test_an_event_in_reach_extends_its_session(self):
        merger = two_visits()
        verdict = merger.observe("user-1", 14)
        assert verdict == (
            "user-1: session extends to [10, 14]"
        )

    def test_keys_keep_separate_biographies(self):
        merger = two_visits()
        assert "new session" in merger.observe("user-2", 11)

    def test_a_gapless_merger_is_refused(self):
        with pytest.raises(Invalid):
            SessionMerger(gap=0)


class TestTheBridge:
    def test_the_bridge_collapses_two_into_one(self):
        merger = SessionMerger(gap=5)
        merger.observe("user-1", 10)
        merger.observe("user-1", 18)
        verdict = merger.observe("user-1", 14)
        assert (
            "the bridge at 14 collapses [10, 10] and "
            "[18, 18] into [10, 18]"
        ) in verdict
        assert "one session all along" in verdict
        spans = merger.spans["user-1"]
        assert len(spans) == 1
        assert spans[0].count == 3

    def test_the_correction_feed_names_what_it_merged(self):
        merger = SessionMerger(gap=5)
        merger.observe("user-1", 10)
        merger.observe("user-1", 18)
        merger.observe("user-1", 14)
        feed = merger.correction_feed()
        assert feed.startswith("1 retroactive merge(s)")
        assert "rows that never happened" in feed

    def test_a_bridgeless_history_stands_alone(self):
        assert two_visits().correction_feed() == (
            "no merges; every session stood alone"
        )

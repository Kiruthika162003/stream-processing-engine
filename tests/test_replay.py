from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.replay import ReplayHarness, backfill_drill


class TestTheTwoModes:
    def test_live_mode_may_consult_the_clock(self):
        harness = ReplayHarness(mode="live")
        assert "may consult" in harness.wall_clock("timeouts")
        assert harness.wall_clock_reads == 1

    def test_replay_forbids_the_clock_with_the_caller_named(self):
        harness = ReplayHarness(
            mode="replay", replay_date="2026-09-08"
        )
        with pytest.raises(Halted) as caught:
            harness.wall_clock("rate-limiter")
        message = str(caught.value)
        assert message.startswith(
            "rate-limiter read the wall clock during replay"
        )
        assert "never in the code you are looking at" in message

    def test_a_dateless_replay_is_refused(self):
        with pytest.raises(Invalid):
            ReplayHarness(mode="replay")


class TestTagging:
    def test_replay_output_wears_both_dates(self):
        harness = ReplayHarness(
            mode="replay", replay_date="2026-09-08"
        )
        line = harness.emit("[2023-04-01)", 140)
        assert line == (
            "[2023-04-01) = 140 (REPROCESSED 2026-09-08)"
        )

    def test_live_output_stays_plain(self):
        harness = ReplayHarness(mode="live")
        assert harness.emit("[now)", 5) == "[now) = 5"

    def test_provenance_answers_computed_when_by_which_code(self):
        harness = ReplayHarness(
            mode="replay", replay_date="2026-09-08"
        )
        answer = harness.provenance_answer()
        assert "a date and an author" in answer


class TestTheDrill:
    def test_the_drill_shows_the_door_holding(self):
        story = backfill_drill()
        assert "'[2023-04-01) = 100'" in story
        assert "REPROCESSED 2026-09-08" in story
        assert "stopped at the door in replay" in story

from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.pauseresume import PausableConsumer


def consumer() -> PausableConsumer:
    built = PausableConsumer(name="etl-1")
    built.consume(50)
    built.finish_batch()
    return built


class TestThePause:
    def test_the_pause_finishes_the_batch_first(self):
        chosen = consumer()
        chosen.consume(10)
        verdict = chosen.pause(now=100, window=60)
        assert "in-flight batch finished first" in verdict
        assert "bookmark at 60" in verdict
        assert "no rebalance fires for a planned absence" in (
            verdict
        )

    def test_a_paused_consumer_refuses_intake(self):
        chosen = consumer()
        chosen.pause(now=100, window=60)
        with pytest.raises(Invalid) as caught:
            chosen.consume(5)
        assert "not a mess, a bookmark" in str(caught.value)


class TestTheResume:
    def test_resume_reports_the_gap(self):
        chosen = consumer()
        chosen.pause(now=100, window=60)
        verdict = chosen.resume(stream_head=210)
        assert verdict == (
            "etl-1 resumes from 50, 160 event(s) to catch "
            "up; the bookmark held"
        )

    def test_resuming_the_unpaused_is_refused(self):
        with pytest.raises(Invalid):
            consumer().resume(stream_head=100)


class TestTheOverdueCheck:
    def test_inside_the_window_is_maintenance(self):
        chosen = consumer()
        chosen.pause(now=100, window=60)
        assert (
            "paused with 40 tick(s) left"
        ) in chosen.overdue_check(now=120)

    def test_past_the_window_the_label_comes_off(self):
        chosen = consumer()
        chosen.pause(now=100, window=60)
        verdict = chosen.overdue_check(now=200)
        assert "40 tick(s) past its window" in verdict
        assert "incident wearing a maintenance label" in verdict

    def test_a_running_consumer_is_just_running(self):
        assert consumer().overdue_check(now=5) == (
            "etl-1 is running"
        )

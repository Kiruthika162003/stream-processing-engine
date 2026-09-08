from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.readmodel import ReadModel


def applied_model() -> ReadModel:
    model = ReadModel()
    for position, delta in enumerate((100, -30, 50)):
        model.apply(position, "acct-1", delta)
    return model


class TestTheView:
    def test_events_apply_in_order_only(self):
        model = applied_model()
        with pytest.raises(Invalid):
            model.apply(9, "acct-1", 5)

    def test_a_current_answer_says_so(self):
        model = applied_model()
        assert model.query("acct-1", stream_head=3) == (
            "acct-1: 120, current with the stream"
        )

    def test_a_stale_answer_carries_its_age(self):
        model = applied_model()
        answer = model.query("acct-1", stream_head=33)
        assert answer.startswith(
            "acct-1: 120 as of 30 event(s) ago"
        )
        assert "the caller decides what stale means" in answer

    def test_an_unknown_key_reads_zero_honestly(self):
        model = applied_model()
        assert "ghost: 0" in model.query(
            "ghost", stream_head=3
        )


class TestTheRebuild:
    def test_mid_rebuild_answers_are_refused_as_wrong(self):
        model = applied_model()
        model.begin_rebuild()
        with pytest.raises(Halted) as caught:
            model.query("acct-1", stream_head=10)
        assert "not be stale, it would be wrong" in str(
            caught.value
        )

    def test_the_rebuild_replays_to_the_same_view(self):
        model = applied_model()
        before = dict(model.balances)
        model.begin_rebuild()
        verdict = model.finish_rebuild(
            [("acct-1", 100), ("acct-1", -30), ("acct-1", 50)]
        )
        assert verdict == (
            "rebuilt through 2 from 3 event(s); answering "
            "again"
        )
        assert model.balances == before

    def test_finishing_without_beginning_is_refused(self):
        with pytest.raises(Invalid):
            applied_model().finish_rebuild([])

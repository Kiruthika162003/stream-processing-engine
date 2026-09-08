from __future__ import annotations

import pytest

from rill.asyncorder import AsyncEmitter
from rill.errors import Invalid


class TestUnordered:
    def test_each_answer_ships_the_moment_it_lands(self):
        emitter = AsyncEmitter(mode="unordered")
        first = emitter.submit("a")
        second = emitter.submit("b")
        assert emitter.complete(second, "B") == ["B"]
        assert emitter.complete(first, "A") == ["A"]

    def test_unordered_never_buffers(self):
        emitter = AsyncEmitter(mode="unordered")
        token = emitter.submit("a")
        emitter.complete(token, "A")
        assert emitter.buffered() == 0


class TestOrdered:
    def test_a_fast_answer_waits_for_the_slow_one_ahead(self):
        emitter = AsyncEmitter(mode="ordered")
        first = emitter.submit("a")
        second = emitter.submit("b")
        assert emitter.complete(second, "B") == []
        assert emitter.buffered() == 1
        assert emitter.complete(first, "A") == ["A", "B"]

    def test_the_buffer_swells_to_the_events_behind_the_stall(self):
        emitter = AsyncEmitter(mode="ordered")
        head = emitter.submit("head")
        rest = [emitter.submit(f"e{n}") for n in range(4)]
        for token in reversed(rest):
            emitter.complete(token, token)
        assert emitter.peak_buffer() == 4
        drained = emitter.complete(head, "head")
        assert drained[0] == "head"
        assert len(drained) == 5

    def test_in_order_completion_releases_immediately(self):
        emitter = AsyncEmitter(mode="ordered")
        first = emitter.submit("a")
        second = emitter.submit("b")
        assert emitter.complete(first, "A") == ["A"]
        assert emitter.complete(second, "B") == ["B"]


class TestRefusals:
    def test_an_unknown_mode_is_refused(self):
        with pytest.raises(Invalid):
            AsyncEmitter(mode="whenever")

    def test_completing_an_unknown_token_is_refused(self):
        emitter = AsyncEmitter(mode="ordered")
        with pytest.raises(Invalid):
            emitter.complete(7, "ghost")

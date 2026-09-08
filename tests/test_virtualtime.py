from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.virtualtime import VirtualClock


class TestTheClock:
    def test_a_week_costs_a_millisecond(self):
        clock = VirtualClock()
        log: list[int] = []
        for day in range(7):
            clock.call_at(
                day * 24, f"day-{day}", lambda d=day: log.append(d)
            )
        fired = clock.advance_to(7 * 24)
        assert len(fired) == 7
        assert log == list(range(7))

    def test_callbacks_see_their_own_instant(self):
        clock = VirtualClock()
        seen: list[int] = []
        clock.call_at(10, "a", lambda: seen.append(clock.now))
        clock.call_at(20, "b", lambda: seen.append(clock.now))
        clock.advance_to(50)
        assert seen == [10, 20]
        assert clock.now == 50

    def test_a_callback_may_schedule_the_next(self):
        clock = VirtualClock()
        chain: list[str] = []

        def first() -> None:
            chain.append("first")
            clock.call_at(15, "second", lambda: chain.append("second"))

        clock.call_at(10, "first", first)
        clock.advance_to(30)
        assert chain == ["first", "second"]

    def test_the_past_is_not_a_venue(self):
        clock = VirtualClock()
        clock.advance_to(50)
        with pytest.raises(Invalid):
            clock.call_at(10, "late", lambda: None)
        with pytest.raises(Invalid):
            clock.advance_to(20)


class TestTheDiscipline:
    def test_the_wall_clock_ask_is_named_and_counted(self):
        clock = VirtualClock()
        with pytest.raises(Invalid) as caught:
            clock.wall_clock()
        assert "where flaky tests come from" in str(caught.value)
        audit = clock.audit()
        assert "1 wall-clock ask(s)" in audit
        assert "the only acceptable second number is zero" in (
            audit
        )

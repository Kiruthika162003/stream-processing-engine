from __future__ import annotations

import pytest

from rill.decay import DecayingCounter
from rill.errors import Invalid


def counter() -> DecayingCounter:
    chosen = DecayingCounter(half_life=10)
    for _ in range(3):
        chosen.add(now=0)
    return chosen


class TestDecay:
    def test_the_value_halves_each_half_life(self):
        chosen = counter()
        assert chosen.read(0) == pytest.approx(3.0)
        assert chosen.read(10) == pytest.approx(1.5)
        assert chosen.read(20) == pytest.approx(0.75)

    def test_adding_decays_the_old_value_first(self):
        chosen = counter()
        chosen.add(now=10)
        assert chosen.read(10) == pytest.approx(2.5)

    def test_a_counter_cannot_read_the_past(self):
        chosen = counter()
        chosen.add(now=50)
        with pytest.raises(Invalid):
            chosen.read(10)

    def test_a_zero_half_life_is_refused(self):
        with pytest.raises(Invalid):
            DecayingCounter(half_life=0)


class TestComparison:
    def test_a_stale_large_value_loses_to_a_fresh_smaller_one(self):
        stale = DecayingCounter(half_life=10)
        for _ in range(8):
            stale.add(now=0)
        fresh = DecayingCounter(half_life=10)
        for _ in range(3):
            fresh.add(now=30)
        verdict = stale.compare(fresh, now=30)
        assert "the other counter leads" in verdict
        assert "decayed to 30" in verdict
        assert "has actually faded less" in verdict

    def test_the_tie_is_reported_at_the_query_time(self):
        a = DecayingCounter(half_life=10)
        a.add(now=5, weight=2.0)
        b = DecayingCounter(half_life=10)
        b.add(now=5, weight=2.0)
        assert "tied at 2.00, both decayed to 5" in a.compare(
            b, now=5
        )

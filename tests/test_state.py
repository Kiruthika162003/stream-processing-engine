from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.state import KeyedState


def store() -> KeyedState:
    built = KeyedState(ttl=10)
    built.put("hot", 5, now=100)
    built.put("cold", 7, now=80)
    return built


class TestTheStore:
    def test_puts_and_gets_round_trip(self):
        chosen = store()
        assert chosen.get("hot") == (5, "held")

    def test_a_keyless_put_is_a_global(self):
        with pytest.raises(Invalid):
            store().put("", 1, now=0)

    def test_a_zero_ttl_is_refused_as_a_leak(self):
        with pytest.raises(Invalid) as caught:
            KeyedState(ttl=0)
        assert "leak with a use case" in str(caught.value)


class TestExpiry:
    def test_the_sweep_reclaims_and_reports_its_share(self):
        chosen = store()
        verdict = chosen.sweep(now=100)
        assert verdict.startswith(
            "swept 1 key(s) (50% of the store), 1 remain"
        )
        assert "shrug in an incident review" in verdict

    def test_expired_is_a_different_answer_from_never_seen(self):
        chosen = store()
        chosen.sweep(now=100)
        value, story = chosen.get("cold")
        assert value is None
        assert story.startswith("expired")
        assert chosen.get("ghost") == (None, "never seen")

    def test_a_touch_revives_the_clock(self):
        chosen = store()
        chosen.put("cold", 8, now=99)
        assert "nothing idle" in chosen.sweep(now=100)

    def test_a_rewrite_clears_the_expired_mark(self):
        chosen = store()
        chosen.sweep(now=100)
        chosen.put("cold", 9, now=101)
        assert chosen.get("cold") == (9, "held")

    def test_the_census_totals_the_life_of_the_store(self):
        chosen = store()
        chosen.sweep(now=100)
        assert chosen.census() == (
            "1 live key(s), 1 swept over the store's life, "
            "ttl 10"
        )

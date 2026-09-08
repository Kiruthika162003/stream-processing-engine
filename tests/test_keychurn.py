from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.keychurn import ChurnCensus


class TestTheCensus:
    def test_the_window_splits_novel_from_returning(self):
        census = ChurnCensus()
        census.observe_window(["a", "b", "c"])
        verdict = census.observe_window(["a", "d"])
        assert verdict == (
            "window: 1 novel, 1 returning (50% churn)"
        )

    def test_an_empty_window_is_refused(self):
        with pytest.raises(Invalid):
            ChurnCensus().observe_window([])


class TestTheRegime:
    def test_the_session_stream_is_churning(self):
        census = ChurnCensus()
        for window in range(5):
            census.observe_window(
                [f"session-{window}-{n}" for n in range(10)]
            )
        assert "churning at 100% novel" in census.regime()
        assert "runs out of memory on day three" in (
            census.regime()
        )

    def test_the_user_stream_plateaus(self):
        census = ChurnCensus()
        users = [f"user-{n}" for n in range(20)]
        for _ in range(5):
            census.observe_window(users)
        regime = census.regime()
        assert "plateauing at 0% novel" in regime
        assert "over-provisions" in regime

    def test_the_mixed_stream_admits_uncertainty(self):
        census = ChurnCensus()
        base = [f"user-{n}" for n in range(7)]
        census.observe_window(base)
        for window in range(3):
            census.observe_window(
                base + [f"new-{window}-{n}" for n in range(3)]
            )
        regime = census.regime()
        assert "mixed at 30% novel" in regime
        assert "the event rate cannot tell them apart" in regime

    def test_an_unobserved_census_has_no_regime(self):
        with pytest.raises(Invalid):
            ChurnCensus().novel_share()

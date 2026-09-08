from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.watermarkgen import PercentileWatermark, strategy_advice


def loaded() -> PercentileWatermark:
    mark = PercentileWatermark(coverage_percentile=90)
    for event_time in (100, 95, 98, 60, 102, 101, 99, 97, 103, 50):
        mark.observe(event_time)
    return mark


class TestThePercentileMargin:
    def test_the_margin_covers_the_declared_percentile(self):
        mark = loaded()
        assert mark.margin() >= 40

    def test_the_watermark_trails_by_the_margin(self):
        mark = loaded()
        assert mark.watermark() == mark.max_seen - mark.margin()

    def test_the_margin_adapts_note_explains_itself(self):
        note = loaded().adapts_note()
        assert "covers the 90th percentile" in note
        assert "guessed once and left wrong" in note

    def test_a_wild_percentile_is_refused(self):
        with pytest.raises(Invalid):
            PercentileWatermark(coverage_percentile=30)

    def test_a_marginless_sampleless_watermark_is_refused(self):
        with pytest.raises(Invalid):
            PercentileWatermark(coverage_percentile=90).margin()


class TestStrategyAdvice:
    def test_the_stable_stream_wants_a_fixed_margin(self):
        advice = strategy_advice("stable")
        assert "small fixed margin" in advice
        assert "stragglers that never come" in advice

    def test_the_bursty_stream_wants_a_percentile(self):
        advice = strategy_advice("bursty")
        assert "breathes" in advice
        assert "drops a tenth of the events" in advice

    def test_an_unknown_stability_class_is_refused(self):
        with pytest.raises(Invalid) as caught:
            strategy_advice("chaotic")
        assert "the strategy is a choice, not a default" in str(
            caught.value
        )

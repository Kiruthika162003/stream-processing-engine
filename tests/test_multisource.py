from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.multisource import MultiSourceWatermark


def four_partitions() -> MultiSourceWatermark:
    combined = MultiSourceWatermark(idle_timeout=10)
    for number in range(4):
        combined.add_source(f"p{number}")
    return combined


class TestTheMinimum:
    def test_the_combined_watermark_is_the_minimum(self):
        combined = four_partitions()
        for number, event_time in enumerate((20, 15, 30, 25)):
            combined.speak(f"p{number}", event_time, now=0)
        assert combined.combined() == 15

    def test_the_census_names_the_holdback(self):
        combined = four_partitions()
        for number, event_time in enumerate((20, 15, 30, 25)):
            combined.speak(f"p{number}", event_time, now=0)
        census = combined.holdback_census()
        assert census.startswith(
            "p1 holds the watermark back by 5 tick(s)"
        )
        assert "this is a ticket" in census

    def test_a_stranger_source_is_refused(self):
        with pytest.raises(Invalid):
            four_partitions().speak("ghost", 5, now=0)


class TestIdleness:
    def test_the_quiet_partition_is_excused(self):
        combined = four_partitions()
        for number, event_time in enumerate((20, 5, 30, 25)):
            combined.speak(f"p{number}", event_time, now=0)
        marked = combined.mark_idle(now=15)
        assert marked == [
            "p0 silent for 15, excused from the minimum",
            "p1 silent for 15, excused from the minimum",
            "p2 silent for 15, excused from the minimum",
            "p3 silent for 15, excused from the minimum",
        ]

    def test_excusing_the_quiet_one_frees_the_watermark(self):
        combined = four_partitions()
        for number, event_time in enumerate((20, 5, 30, 25)):
            combined.speak(f"p{number}", event_time, now=0)
        combined.speak("p0", 21, now=14)
        combined.speak("p2", 31, now=14)
        combined.speak("p3", 26, now=14)
        combined.mark_idle(now=15)
        assert combined.combined() == 21

    def test_the_rejoiner_is_told_how_far_behind_it_is(self):
        combined = four_partitions()
        for number, event_time in enumerate((20, 5, 30, 25)):
            combined.speak(f"p{number}", event_time, now=0)
        for name, event_time in (("p0", 21), ("p2", 31), ("p3", 26)):
            combined.speak(name, event_time, now=14)
        combined.mark_idle(now=15)
        verdict = combined.speak("p1", 6, now=16)
        assert verdict.startswith("p1 rejoins the minimum")
        assert "15 tick(s) behind the combined watermark" in verdict

    def test_all_idle_means_no_opinion_about_time(self):
        combined = four_partitions()
        for number in range(4):
            combined.speak(f"p{number}", 10, now=0)
        combined.mark_idle(now=50)
        with pytest.raises(Invalid) as caught:
            combined.combined()
        assert "no opinion about time" in str(caught.value)

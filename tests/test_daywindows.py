from __future__ import annotations

import pytest

from rill.daywindows import CalendarDays
from rill.errors import Invalid


def dst_week() -> CalendarDays:
    return CalendarDays(
        day_starts=[
            ("friday", 0),
            ("saturday", 24),
            ("sunday-springforward", 48),
            ("monday", 71),
            ("tuesday", 95),
        ]
    )


class TestAssignment:
    def test_events_land_on_their_calendar_day(self):
        calendar = dst_week()
        assert calendar.assign(30) == "saturday"
        assert calendar.assign(70) == "sunday-springforward"
        assert calendar.assign(71) == "monday"

    def test_the_short_day_holds_only_its_hours(self):
        calendar = dst_week()
        assert calendar.assign(48) == "sunday-springforward"
        assert calendar.assign(94) == "monday"

    def test_outside_the_calendar_is_refused(self):
        with pytest.raises(Invalid):
            dst_week().assign(500)


class TestTheTable:
    def test_gaps_and_overlaps_are_rejected_at_load(self):
        with pytest.raises(Invalid) as caught:
            CalendarDays(
                day_starts=[("a", 0), ("b", 24), ("c", 20)]
            )
        assert "without even the courtesy of being late" in (
            str(caught.value)
        )

    def test_the_report_attaches_the_sentence_to_the_row(self):
        report = dst_week().irregular_report()
        assert report.startswith("1 irregular day(s)")
        assert (
            "sunday-springforward: 23 hour(s), spring "
            "forward, short on purpose"
        ) in report

    def test_a_boring_calendar_says_so(self):
        calendar = CalendarDays(
            day_starts=[("a", 0), ("b", 24), ("c", 48)]
        )
        assert calendar.irregular_report() == (
            "every day ran its standard 24"
        )

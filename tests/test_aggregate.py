from __future__ import annotations

import pytest

from rill.aggregate import WindowedSum
from rill.errors import Invalid
from rill.events import Event
from rill.watermark import BoundedWatermark


def summer(bound: int = 2) -> WindowedSum:
    return WindowedSum(
        window_size=10,
        watermark=BoundedWatermark(lateness_bound=bound),
    )


def at(key: str, value: int, event_time: int) -> Event:
    return Event(
        key=key, value=value, event_time=event_time,
        arrival=event_time,
    )


class TestAccumulation:
    def test_the_pane_folds_in_any_order(self):
        agg = summer()
        agg.feed(at("a", 3, 15))
        agg.feed(at("a", 4, 11))
        assert agg.panes == {
            ("a", next(iter(agg.panes))[1]): 7
        }

    def test_the_watermark_speaks_the_answer(self):
        agg = summer(bound=2)
        agg.feed(at("a", 3, 15))
        notes = agg.feed(at("a", 1, 23))
        assert notes == [
            "a [10, 20) = 3; the watermark passed, the pane "
            "seals"
        ]
        assert agg.fired == ["a[10, 20)=3"]

    def test_keys_keep_separate_panes(self):
        agg = summer(bound=0)
        agg.feed(at("a", 3, 15))
        agg.feed(at("b", 5, 16))
        notes = agg.feed(at("c", 1, 31))
        assert any("a [10, 20) = 3" in note for note in notes)
        assert any("b [10, 20) = 5" in note for note in notes)

    def test_a_sizeless_window_is_refused(self):
        with pytest.raises(Invalid):
            WindowedSum(
                window_size=0,
                watermark=BoundedWatermark(lateness_bound=1),
            )


class TestSealing:
    def test_late_events_are_named_never_folded(self):
        agg = summer(bound=2)
        agg.feed(at("a", 3, 15))
        agg.feed(at("a", 1, 23))
        notes = agg.feed(at("a", 9, 12))
        assert len(notes) == 1
        assert "never folded" in notes[0]
        assert agg.refused_late == ["a@12"]
        assert agg.fired == ["a[10, 20)=3"]

    def test_the_ledger_reports_the_fit_of_the_bet(self):
        agg = summer(bound=2)
        agg.feed(at("a", 3, 15))
        agg.feed(at("a", 1, 23))
        agg.feed(at("a", 9, 12))
        ledger = agg.ledger()
        assert ledger.startswith(
            "1 pane(s) fired, 2 event(s) folded, 1 late "
            "refusal(s), 1 pane(s) still accumulating"
        )

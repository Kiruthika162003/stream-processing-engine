from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.loadshed import LoadShedder


class TestPriorityShedding:
    def test_high_priority_always_survives(self):
        shedder = LoadShedder(mode="priority", keep_percent=1)
        assert shedder.admit("evt-1", priority="high")
        assert not shedder.admit("evt-2", priority="normal")

    def test_the_alerting_note_keeps_every_high(self):
        shedder = LoadShedder(mode="priority", keep_percent=1)
        shedder.admit("a", priority="high")
        shedder.admit("b", priority="normal")
        note = shedder.denominator_note()
        assert "keeps every high-priority event" in note


class TestSamplingShedding:
    def test_sampling_keeps_a_deterministic_fraction(self):
        shedder = LoadShedder(mode="sampling", keep_percent=20)
        kept = sum(
            1
            for number in range(500)
            if shedder.admit(f"evt-{number}")
        )
        assert 60 < kept < 140

    def test_the_metrics_note_demands_denominator_scaling(self):
        shedder = LoadShedder(mode="sampling", keep_percent=20)
        for number in range(100):
            shedder.admit(f"evt-{number}")
        note = shedder.denominator_note()
        assert "the metrics consumer must scale by this" in note
        assert "nobody announced" in note


class TestTheContract:
    def test_the_wrong_mode_is_refused(self):
        with pytest.raises(Invalid) as caught:
            LoadShedder(mode="vibes", keep_percent=50)
        assert "worse than not shedding" in str(caught.value)

    def test_the_loss_report_categorizes_drops(self):
        shedder = LoadShedder(mode="priority", keep_percent=1)
        shedder.admit("a", priority="normal")
        shedder.admit("b", priority="normal")
        report = shedder.loss_report()
        assert "low-priority: 2" in report
        assert "never a silent gap" in report

    def test_nothing_offered_has_no_denominator(self):
        with pytest.raises(Invalid):
            LoadShedder(
                mode="sampling", keep_percent=10
            ).denominator_note()

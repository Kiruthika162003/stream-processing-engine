from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.triage import TABLE, full_card, triage


class TestTheTable:
    def test_each_symptom_maps_in_one_hop(self):
        verdict = triage("watermark-stuck")
        assert verdict == (
            "watermark-stuck -> multisource clock; first "
            "question: which partition went quiet, and is it "
            "idle or dead"
        )

    def test_the_dozen_are_all_answerable(self):
        for symptom in TABLE:
            line = triage(symptom)
            assert "->" in line
            assert "first question:" in line

    def test_its_slow_is_sharpened_first(self):
        with pytest.raises(Invalid) as caught:
            triage("its-slow")
        assert "three different organs" in str(caught.value)

    def test_unknown_symptoms_list_the_known(self):
        with pytest.raises(Invalid) as caught:
            triage("gremlins")
        assert "lag-rising" in str(caught.value)


class TestTheCard:
    def test_the_card_prints_every_row(self):
        card = full_card()
        for symptom in TABLE:
            assert symptom in card
        assert "ten-minute diagnosis" in card

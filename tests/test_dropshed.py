from __future__ import annotations

import pytest

from rill.dropshed import LoadShedder
from rill.errors import Invalid

TIERS = {"payment": 3, "order": 2, "telemetry": 1}


def shedder() -> LoadShedder:
    return LoadShedder(tiers=dict(TIERS), capacity_per_tick=100)


class TestShedding:
    def test_a_calm_tick_admits_everything(self):
        chosen = shedder()
        verdict = chosen.tick(
            {"payment": 10, "order": 20, "telemetry": 30}
        )
        assert verdict == (
            "everything admitted; no shedding this tick"
        )

    def test_the_bottom_tier_sheds_first(self):
        chosen = shedder()
        verdict = chosen.tick(
            {"payment": 40, "order": 40, "telemetry": 60}
        )
        assert verdict == "shed 40 telemetry (tier 1)"
        assert chosen.admitted["payment"] == 40
        assert chosen.admitted["telemetry"] == 20

    def test_payments_are_the_last_to_go(self):
        chosen = shedder()
        verdict = chosen.tick(
            {"payment": 150, "order": 10, "telemetry": 10}
        )
        assert "shed 50 payment" in verdict
        assert "shed 10 order" in verdict
        assert chosen.admitted["payment"] == 100

    def test_the_unranked_class_is_refused(self):
        chosen = shedder()
        with pytest.raises(Invalid) as caught:
            chosen.tick({"mystery": 5})
        assert "dropped by accident" in str(caught.value)


class TestTheFootnote:
    def test_the_footnote_is_a_decision_not_an_accident(self):
        chosen = shedder()
        chosen.tick(
            {"payment": 40, "order": 40, "telemetry": 60}
        )
        footnote = chosen.incident_footnote()
        assert footnote.startswith(
            "dropped 0 payment, 0 order, 40 telemetry"
        )
        assert "made in advance" in footnote

    def test_an_untouched_shedder_has_no_footnote(self):
        with pytest.raises(Invalid):
            shedder().incident_footnote()

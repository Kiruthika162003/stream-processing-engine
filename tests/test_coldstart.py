from __future__ import annotations

import pytest

from rill.coldstart import ColdStart
from rill.errors import Invalid


def stream() -> ColdStart:
    return ColdStart(
        retained_events=100000,
        snapshot_position=95000,
        head_position=100000,
    )


class TestTheThreeDoors:
    def test_earliest_pays_the_whole_history(self):
        bill, nature = stream().price("earliest")
        assert bill == 100000
        assert "re-fires a week of alerts" in nature

    def test_latest_is_cheap_amnesia(self):
        bill, nature = stream().price("latest")
        assert bill == 0
        assert "billing from amnesia" in nature

    def test_snapshot_is_the_medium_bill(self):
        bill, nature = stream().price("snapshot")
        assert bill == 5000
        assert "the medium bill" in nature

    def test_a_fourth_door_does_not_exist(self):
        with pytest.raises(Invalid):
            stream().price("wherever")

    def test_the_snapshot_cannot_lead_the_head(self):
        with pytest.raises(Invalid):
            ColdStart(
                retained_events=10,
                snapshot_position=50,
                head_position=40,
            )


class TestTheRecord:
    def test_the_decision_survives_its_chooser(self):
        record = stream().decision_record(
            "snapshot",
            "billing-consumer",
            "invoices need complete state, replay too dear",
        )
        assert record.startswith(
            "billing-consumer starts at snapshot: 5000 "
            "event(s) to process"
        )
        assert "reason: invoices need complete state" in record

    def test_a_reasonless_choice_is_refused(self):
        with pytest.raises(Invalid) as caught:
            stream().decision_record(
                "latest", "alerting", " "
            )
        assert "config flag's name alone" in str(caught.value)

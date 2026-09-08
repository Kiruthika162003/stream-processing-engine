from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.forgetme import Eraser


def eraser() -> Eraser:
    built = Eraser(retention_days=30)
    built.open_request("user-77")
    return built


class TestTheChecklist:
    def test_the_request_opens_with_its_stations(self):
        built = Eraser(retention_days=30)
        verdict = built.open_request("user-9")
        assert "3 station(s) on the checklist" in verdict

    def test_stations_count_down(self):
        chosen = eraser()
        verdict = chosen.complete_station(
            "user-77", "live-state"
        )
        assert verdict == "user-77: live-state purged, 2 to go"

    def test_unknown_stations_are_refused(self):
        with pytest.raises(Invalid):
            eraser().complete_station("user-77", "backups")


class TestTheCertificate:
    def test_early_certification_is_refused_with_the_reason(self):
        chosen = eraser()
        chosen.complete_station("user-77", "live-state")
        with pytest.raises(Invalid) as caught:
            chosen.certify("user-77", today="2026-02-01")
        message = str(caught.value)
        assert "compacted-log, read-models unfinished" in message
        assert "disproven in discovery" in message

    def test_the_full_certificate_names_the_tail(self):
        chosen = eraser()
        for station in (
            "live-state", "compacted-log", "read-models"
        ):
            chosen.complete_station("user-77", station)
        certificate = chosen.certify(
            "user-77", today="2026-02-01"
        )
        assert certificate.startswith(
            "user-77: deleted everywhere except the 30-day "
            "raw log"
        )
        assert "a sentence legal can work with" in certificate
        assert chosen.certified == ["user-77"]

    def test_double_requests_are_refused(self):
        chosen = eraser()
        with pytest.raises(Invalid):
            chosen.open_request("user-77")

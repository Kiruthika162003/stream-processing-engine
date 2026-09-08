from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.tieredlog import TieredLog


def aged_log() -> TieredLog:
    log = TieredLog(offload_age=100)
    log.append(500)
    log.offload(slowest_consumer=350)
    return log


class TestTheBoundary:
    def test_offload_respects_age_and_the_slowest(self):
        log = aged_log()
        assert log.boundary == 350
        verdict = log.offload(slowest_consumer=500)
        assert "boundary now 400" in verdict
        assert "converts lag into a cliff" in verdict

    def test_the_boundary_holds_when_nothing_qualifies(self):
        log = TieredLog(offload_age=100)
        log.append(50)
        assert "boundary holds at 0" in log.offload(
            slowest_consumer=50
        )


class TestTheReadPath:
    def test_hot_and_cold_reads_admit_the_difference(self):
        log = aged_log()
        hot = log.read("live", 400)
        cold = log.read("backfill", 100)
        assert hot == "live: hot read, 1 tick(s)"
        assert cold.startswith("backfill: cold read, 5 tick(s)")
        assert "aged, not regressed" in cold

    def test_the_head_is_not_readable(self):
        with pytest.raises(Invalid):
            aged_log().read("eager", 500)


class TestTheCrossing:
    def test_the_crossing_report_reads_a_graph_not_a_bug(self):
        log = aged_log()
        report = log.crossing_report("backfill", 200)
        assert (
            "150 position(s) from the crossing"
        ) in report
        assert "it has aged" in report

    def test_the_hot_side_serves_at_disk_speed(self):
        assert "serving at disk speed" in (
            aged_log().crossing_report("live", 450)
        )

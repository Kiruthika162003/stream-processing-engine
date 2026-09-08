from __future__ import annotations

from examples import reliabilityday


class TestReliabilityDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert reliabilityday.main() == 0
        out = capsys.readouterr().out
        assert (
            "order-1 fully acked: every descendant done"
        ) in out
        assert "txn-1 write suppressed" in out
        assert "kafka-in DEAD: no heartbeat for 100" in out
        assert "naive peaks at 4569 (4.6x real traffic)" in out
        assert "shed to 150 did nothing" in out
        assert "recovered: shed below 100 to 80" in out

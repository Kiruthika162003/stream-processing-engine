from __future__ import annotations

from examples import opsweek


class TestOpsWeek:
    def test_the_week_reads_end_to_end(self, capsys):
        assert opsweek.main() == 0
        out = capsys.readouterr().out
        assert "STALLED: watermark frozen at 100" in out
        assert (
            "trending-topic spread across 4 sub-partition(s)"
        ) in out
        assert "recombined to 400" in out
        assert (
            "1 split-brain assignment(s) refused by term"
        ) in out
        assert "PROMOTE: 34 keys compared, agreement 100%" in out
        assert (
            "events 8400 through 9100 were recomputed"
        ) in out

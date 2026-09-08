from __future__ import annotations

from examples import lagday


class TestLagDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert lagday.main() == 0
        out = capsys.readouterr().out
        assert (
            "FALLING BEHIND: lag 160 and growing 40 per window"
        ) in out
        assert "a batch job that has not admitted it yet" in out
        assert "[6] channel-2 filled" in out
        assert "attributed to the sink below it" in out
        assert "1 record(s) waiting for a human:" in out
        assert (
            "billing-consumer CRITICAL: data loss in 8 "
            "tick(s)"
        ) in out
        assert "1 gap event(s) on record" in out
        assert (
            "catching up: lag 40, surplus 40 per window, "
            "caught up in 1 window(s)"
        ) in out

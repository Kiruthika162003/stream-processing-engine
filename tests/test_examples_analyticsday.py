from __future__ import annotations

from examples import analyticsday


class TestAnalyticsDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert analyticsday.main() == 0
        out = capsys.readouterr().out
        assert "distinct (+/-" in out
        assert "quoted with its band" in out
        assert "[('home', 500), ('search', 300)]" in out
        assert "the other counter leads 3.00 to 1.00" in out
        assert "mean 105, p50 10, p99 10000" in out

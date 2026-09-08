from __future__ import annotations

from examples import measuresday


class TestMeasuresDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert measuresday.main() == 0
        out = capsys.readouterr().out
        assert "welford 2.0 vs naive 0.0" in out
        assert "a million tenths total 100000.0" in out
        assert "raw 10.0 vs corrected 100.0" in out
        assert "p99 naive 1 vs corrected 485" in out
        assert "usl peak at 31 workers" in out

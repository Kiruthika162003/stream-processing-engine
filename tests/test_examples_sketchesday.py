from __future__ import annotations

from examples import sketchesday


class TestSketchesDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert sketchesday.main() == 0
        out = capsys.readouterr().out
        assert "identical sets similarity 1.0" in out
        assert "three forced increments estimate 7" in out
        assert "hot is a candidate: True" in out
        assert "a lone key reads back 42" in out
        assert "present True, after delete False" in out

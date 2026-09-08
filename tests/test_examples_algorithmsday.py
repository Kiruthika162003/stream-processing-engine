from __future__ import annotations

from examples import algorithmsday


class TestAlgorithmsDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert algorithmsday.main() == 0
        out = capsys.readouterr().out
        assert "best sum 6 over indices 3 to 6" in out
        assert "distances [2, 1, 2, 1, -1]" in out
        assert "majority: 7" in out
        assert "median:   5" in out
        assert "[1, 2, 3, 4, 5, 6, 7, 8, 9]" in out

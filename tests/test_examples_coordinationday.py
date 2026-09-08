from __future__ import annotations

from examples import coordinationday


class TestCoordinationDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert coordinationday.main() == 0
        out = capsys.readouterr().out
        assert "concurrent 3 and 5 merged to 8" in out
        assert "concurrent add survives remove: True" in out
        assert "independent ticks are concurrent" in out
        assert "prior-term commit 0, then 2" in out
        assert "blocked ['a'], decided commit" in out

from __future__ import annotations

from examples import networkday


class TestNetworkDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert networkday.main() == 0
        out = capsys.readouterr().out
        assert "cost 4 via s-a-b-t" in out
        assert "minimum spanning weight 6" in out
        assert "max flow s to t is 18" in out
        assert "largest feedback loop ['A', 'B', 'C']" in out
        assert "single points of failure [('C', 'D')]" in out

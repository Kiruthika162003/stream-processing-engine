from __future__ import annotations

from examples import flakysinkday


class TestFlakySinkDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert flakysinkday.main() == 0
        out = capsys.readouterr().out
        assert "open at the trip, half_open after the cooldown" in out
        assert "spread 0 in lockstep, 60 with jitter" in out
        assert "p99 500 plain, 70 hedged" in out
        assert "victim still served: True" in out
        assert "compensated ['ship', 'charge']" in out

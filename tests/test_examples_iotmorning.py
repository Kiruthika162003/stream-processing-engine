from __future__ import annotations

from examples import iotmorning


class TestIotMorning:
    def test_the_morning_reads_end_to_end(self, capsys):
        assert iotmorning.main() == 0
        out = capsys.readouterr().out
        assert "healthy with nothing to say" in out
        assert "1 dead of 3: basement-cam" in out
        assert "[20): GAP" in out
        assert (
            "7 of 10 window(s) silent (70%): this is a "
            "broken collector"
        ) in out
        assert "bound 2 refuses 10.0%" in out
        assert "bound 6 refuses 0.0%" in out
        assert (
            "factory-gateway: 1 broken promise(s) in 2 "
            "event(s) (50%)"
        ) in out

from __future__ import annotations

from examples import clicknight


class TestClickNight:
    def test_the_night_reads_end_to_end(self, capsys):
        assert clicknight.main() == 0
        out = capsys.readouterr().out
        assert "1 retroactive merge(s)" in out
        assert "visitor-1 ended with [10, 28]" in out
        assert "/home: 4 (overcount at most 0)" in out
        assert (
            "5% full, comfortable; estimate 3 from 8 offer(s)"
        ) in out
        assert "bound 2 refuses 0.0%" in out

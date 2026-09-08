from __future__ import annotations

from examples import fraudnight


class TestFraudNight:
    def test_the_night_reads_end_to_end(self, capsys):
        assert fraudnight.main() == 0
        out = capsys.readouterr().out
        assert (
            "2 charges within tolerance of one auth"
        ) in out
        assert "hiding its losses" in out
        assert "case-442: silence lasted to 110; firing" in out
        assert "2 alert(s) sent, replay refused" in out
        assert (
            "['express: fraud-check-0', 'express: "
            "fraud-check-1', 'standard: metrics-0']"
        ) in out
        assert "4 express to 2 standard (2.0:1" in out

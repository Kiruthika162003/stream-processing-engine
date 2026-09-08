from __future__ import annotations

from examples import firstpipeline


class TestFirstPipeline:
    def test_the_pipeline_reads_end_to_end(self, capsys):
        assert firstpipeline.main() == 0
        out = capsys.readouterr().out
        assert (
            "8 event(s), disorder 2, max skew 18"
        ) in out
        assert (
            "fired:   sensor-a [10, 20) = 16; the watermark "
            "passed, the pane seals"
        ) in out
        assert "sensor-b [10, 20) = 8" in out
        assert (
            "late:    sensor-a=2 happened at 12, seen at 30"
        ) in out
        assert (
            "drop-zeroes: 8 in, 7 out, 1 dropped (zero "
            "readings are sensor hiccups)"
        ) in out
        assert (
            "2 pane(s) fired, 6 event(s) folded, 1 late "
            "refusal(s), 3 pane(s) still accumulating"
        ) in out
        assert "4-10: 1 (100%)" in out

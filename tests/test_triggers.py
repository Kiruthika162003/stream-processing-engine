from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.triggers import TriggeredPane


def pane(mode: str = "accumulating") -> TriggeredPane:
    return TriggeredPane(
        window_label="[0, 60)", interval=10, mode=mode
    )


class TestEarlyFirings:
    def test_the_first_fold_speaks_an_estimate(self):
        chosen = pane()
        line = chosen.fold(5, now=0)
        assert line.startswith("ESTIMATE [0, 60) = 5")
        assert "was warned" in line

    def test_the_interval_gates_the_chatter(self):
        chosen = pane()
        chosen.fold(5, now=0)
        assert chosen.fold(3, now=4) is None
        assert chosen.fold(2, now=10) is not None

    def test_accumulating_repeats_the_running_total(self):
        chosen = pane("accumulating")
        chosen.fold(5, now=0)
        line = chosen.fold(3, now=10)
        assert "= 8 (accumulating)" in line

    def test_discarding_speaks_only_the_delta(self):
        chosen = pane("discarding")
        chosen.fold(5, now=0)
        chosen.fold(3, now=4)
        line = chosen.fold(2, now=10)
        assert "= 5 (discarding)" in line

    def test_the_mode_is_a_constructor_argument(self):
        with pytest.raises(Invalid) as caught:
            pane("both")
        assert "double-counts revenue" in str(caught.value)


class TestTheAnswer:
    def test_the_answer_carries_the_final_label(self):
        chosen = pane()
        chosen.fold(5, now=0)
        chosen.fold(3, now=4)
        line = chosen.on_time()
        assert line.startswith("ANSWER [0, 60) = 8")
        assert "goes in the report" in line

    def test_a_sealed_pane_speaks_no_more(self):
        chosen = pane()
        chosen.fold(5, now=0)
        chosen.on_time()
        with pytest.raises(Invalid):
            chosen.fold(1, now=20)
        with pytest.raises(Invalid):
            chosen.on_time()

    def test_the_transcript_reads_in_order(self):
        chosen = pane()
        chosen.fold(5, now=0)
        chosen.on_time()
        transcript = chosen.transcript()
        assert transcript.splitlines()[0].startswith("ESTIMATE")
        assert transcript.splitlines()[1].startswith("ANSWER")

    def test_the_silent_pane_says_so(self):
        assert pane().transcript() == "[0, 60): silent so far"

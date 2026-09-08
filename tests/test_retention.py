from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.retention import RetentionMargin


def log_margin() -> RetentionMargin:
    return RetentionMargin(retention_span=100)


class TestTheLadder:
    def test_comfortable_is_quiet(self):
        assert log_margin().report_lag("a", 20) == (
            "a comfortable: margin 80"
        )

    def test_tightening_names_the_margin(self):
        assert log_margin().report_lag("b", 70) == (
            "b tightening: 30 tick(s) of margin left"
        )

    def test_critical_carries_the_deadline(self):
        verdict = log_margin().report_lag("c", 92)
        assert verdict.startswith(
            "c CRITICAL: data loss in 8 tick(s)"
        )
        assert "gets a fix deployed" in verdict

    def test_the_gap_records_both_numbers(self):
        margin = log_margin()
        verdict = margin.report_lag("d", 105)
        assert verdict.startswith("d GAP: the tail fell off")
        assert "facts, not archaeology" in verdict
        assert margin.gap_events == [
            "d lost 6 tick(s) of data: lag 105 outran "
            "retention 100"
        ]

    def test_a_retentionless_log_is_a_pipe(self):
        with pytest.raises(Invalid):
            RetentionMargin(retention_span=0)


class TestTheBoard:
    def test_the_board_sorts_the_most_endangered_first(self):
        margin = log_margin()
        margin.report_lag("safe", 10)
        margin.report_lag("risky", 92)
        margin.report_lag("gone", 120)
        board = margin.board()
        lines = board.splitlines()
        assert lines[1] == "  gone: GAP"
        assert lines[2] == "  risky: 8 tick(s) of margin"
        assert lines[3] == "  safe: 90 tick(s) of margin"
        assert "1 gap event(s) on record" in board

    def test_an_empty_board_is_refused(self):
        with pytest.raises(Invalid):
            log_margin().board()

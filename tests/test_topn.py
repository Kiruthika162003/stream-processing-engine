from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.topn import SpaceSaving


def leaderboard() -> SpaceSaving:
    board = SpaceSaving(capacity=3)
    for _ in range(100):
        board.observe("a")
    for _ in range(80):
        board.observe("b")
    for _ in range(60):
        board.observe("c")
    for key in ("d", "e", "f", "g"):
        board.observe(key)
    return board


class TestHeavyHitters:
    def test_the_clear_leaders_are_exact(self):
        board = leaderboard()
        top = board.top(2)
        assert top == [("a", 100), ("b", 80)]
        assert board.overcount.get("a", 0) == 0
        assert board.overcount.get("b", 0) == 0

    def test_the_tail_newcomer_carries_its_overcount(self):
        board = leaderboard()
        third_key, _third_count = board.top(3)[2]
        assert third_key == "g"
        assert board.overcount[third_key] > 0

    def test_a_zero_capacity_board_is_refused(self):
        with pytest.raises(Invalid):
            SpaceSaving(capacity=0)


class TestTheReport:
    def test_the_report_shows_error_bars(self):
        report = leaderboard().report(3)
        assert "a: 100 (exact)" in report
        assert "g: 64 (up to 63 overcounted)" in report
        assert "quoted as exact" in report

    def test_a_key_seen_repeatedly_stays_in_the_board(self):
        board = SpaceSaving(capacity=2)
        for _ in range(10):
            board.observe("steady")
        board.observe("x")
        board.observe("y")
        assert board.counters["steady"] == 10

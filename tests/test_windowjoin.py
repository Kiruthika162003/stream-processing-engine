from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.windowjoin import WindowedJoin


def join() -> WindowedJoin:
    return WindowedJoin(window_size=10)


class TestMatching:
    def test_same_window_events_match(self):
        chosen = join()
        chosen.feed_left(12)
        chosen.feed_right(15)
        assert chosen.matches() == [(12, 15)]

    def test_different_windows_do_not_match(self):
        chosen = join()
        chosen.feed_left(18)
        chosen.feed_right(22)
        assert chosen.matches() == []

    def test_a_sizeless_window_is_refused(self):
        with pytest.raises(Invalid):
            WindowedJoin(window_size=0)


class TestNearMisses:
    def test_the_boundary_straddle_is_a_named_category(self):
        chosen = join()
        chosen.feed_left(19)
        chosen.feed_right(21)
        verdict = chosen.detect_near_misses(tolerance=5)
        assert "1 near-miss(es) split by window edges" in verdict
        assert "not at missing data" in verdict

    def test_aligned_windows_have_no_near_misses(self):
        chosen = join()
        chosen.feed_left(12)
        chosen.feed_right(15)
        assert "the windows align" in chosen.detect_near_misses(
            tolerance=5
        )


class TestSymmetry:
    def test_the_join_is_symmetric(self):
        chosen = join()
        chosen.feed_left(12)
        chosen.feed_left(14)
        chosen.feed_right(15)
        assert "symmetric: the same matches" in (
            chosen.symmetry_check()
        )

    def test_symmetry_holds_across_multiple_windows(self):
        chosen = join()
        for time in (12, 22, 35):
            chosen.feed_left(time)
        for time in (15, 25, 38):
            chosen.feed_right(time)
        assert chosen.symmetry_check().startswith("symmetric")

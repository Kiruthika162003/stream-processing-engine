from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.resequencer import Resequencer


class TestOrdering:
    def test_in_order_arrivals_pass_straight_through(self):
        req = Resequencer(gap_timeout=100)
        assert req.offer(0, "a", now=0) == ["a"]
        assert req.offer(1, "b", now=1) == ["b"]

    def test_an_early_arrival_waits_for_its_predecessor(self):
        req = Resequencer(gap_timeout=100)
        assert req.offer(1, "b", now=0) == []
        assert req.pending() == 1
        assert req.offer(0, "a", now=1) == ["a", "b"]

    def test_a_run_releases_contiguously(self):
        req = Resequencer(gap_timeout=100)
        req.offer(2, "c", now=0)
        req.offer(1, "b", now=0)
        assert req.offer(0, "a", now=0) == ["a", "b", "c"]


class TestGapTimeout:
    def test_a_lost_sequence_stalls_the_stream_before_the_timeout(self):
        req = Resequencer(gap_timeout=100)
        req.offer(1, "b", now=0)
        req.offer(2, "c", now=0)
        assert req.tick(now=50) == []
        assert req.pending() == 2

    def test_the_timeout_skips_the_lost_sequence_and_drains(self):
        req = Resequencer(gap_timeout=100)
        req.offer(1, "b", now=0)
        req.offer(2, "c", now=0)
        assert req.tick(now=100) == ["b", "c"]
        assert req.skipped() == [0]

    def test_the_gap_timer_anchors_to_when_the_gap_first_appeared(self):
        req = Resequencer(gap_timeout=100)
        req.offer(1, "b", now=0)
        assert req.tick(now=99) == []
        assert req.tick(now=100) == ["b"]


class TestRefusals:
    def test_a_nonpositive_timeout_is_refused(self):
        with pytest.raises(Invalid):
            Resequencer(gap_timeout=0)

    def test_a_sequence_below_the_next_is_refused(self):
        req = Resequencer(gap_timeout=100)
        req.offer(0, "a", now=0)
        with pytest.raises(Invalid):
            req.offer(0, "a", now=1)

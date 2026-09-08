from __future__ import annotations

import pytest

from rill.backfillmerge import BackfillMerge
from rill.errors import Invalid


def merge() -> BackfillMerge:
    return BackfillMerge(cutover_position=100)


class TestTheBoundary:
    def test_the_backfill_owns_before_the_cutover(self):
        merger = merge()
        assert merger.from_backfill(50) == (
            "backfill event at 50 counted"
        )

    def test_live_owns_after_the_cutover(self):
        merger = merge()
        assert merger.from_live(150) == (
            "live event at 150 counted"
        )

    def test_the_backfill_event_past_cutover_is_dropped(self):
        merger = merge()
        verdict = merger.from_backfill(150)
        assert "past the cutover, live owns it" in verdict
        assert merger.dropped_live == [150]

    def test_the_live_event_before_cutover_is_dropped(self):
        merger = merge()
        verdict = merger.from_live(50)
        assert "before the cutover, backfill owns it" in verdict
        assert merger.dropped_backfill == [50]


class TestNoDoubleCount:
    def test_the_overlap_is_counted_exactly_once(self):
        merger = merge()
        merger.from_backfill(50)
        merger.from_live(50)
        assert 50 in merger.counted
        assert merger.dropped_backfill == [50]

    def test_bypassing_the_boundary_is_refused(self):
        merger = merge()
        merger.from_backfill(50)
        with pytest.raises(Invalid) as caught:
            merger._count(50, "sneaky")
        assert "the boundary rule was bypassed" in str(
            caught.value
        )

    def test_the_audit_is_justified_by_zero(self):
        merger = merge()
        for position in range(90, 110):
            merger.from_backfill(position)
            merger.from_live(position)
        audit = merger.audit()
        assert "0 double-count(s)" in audit
        assert "that last number being zero" in audit

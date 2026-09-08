from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.watermarkalign import AlignmentGroup


class TestSpread:
    def test_spread_is_the_gap_between_fastest_and_slowest(self):
        group = AlignmentGroup(max_drift=100)
        group.advance("p0", 500)
        group.advance("p1", 120)
        assert group.spread() == 380
        assert group.slowest() == 120


class TestPausing:
    def test_a_partition_past_the_drift_must_pause(self):
        group = AlignmentGroup(max_drift=100)
        group.advance("p0", 500)
        group.advance("p1", 120)
        assert group.paused() == ["p0"]
        assert not group.may_read("p0")

    def test_a_partition_within_the_drift_keeps_reading(self):
        group = AlignmentGroup(max_drift=100)
        group.advance("p0", 200)
        group.advance("p1", 120)
        assert group.paused() == []
        assert group.may_read("p0")

    def test_the_slow_partition_catching_up_releases_the_fast_one(self):
        group = AlignmentGroup(max_drift=100)
        group.advance("p0", 500)
        group.advance("p1", 120)
        assert not group.may_read("p0")
        group.advance("p1", 450)
        assert group.may_read("p0")
        assert group.paused() == []


class TestRefusals:
    def test_a_nonpositive_drift_is_refused(self):
        with pytest.raises(Invalid):
            AlignmentGroup(max_drift=0)

    def test_a_backward_watermark_is_refused(self):
        group = AlignmentGroup(max_drift=100)
        group.advance("p0", 200)
        with pytest.raises(Invalid):
            group.advance("p0", 100)

    def test_spread_before_any_partition_is_refused(self):
        with pytest.raises(Invalid):
            AlignmentGroup(max_drift=100).spread()

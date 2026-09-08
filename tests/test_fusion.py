from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.fusion import Operator, fuse, fusion_report


def chain() -> list[Operator]:
    return [
        Operator("parse", "map"),
        Operator("drop-nulls", "filter"),
        Operator("normalize", "map"),
        Operator("by-user", "keyby"),
        Operator("count", "aggregate"),
    ]


class TestFusing:
    def test_preserving_runs_fuse_together(self):
        groups = fuse(chain())
        assert groups[0] == ["parse", "drop-nulls", "normalize"]

    def test_repartitioning_operators_stand_alone(self):
        groups = fuse(chain())
        assert ["by-user"] in groups
        assert ["count"] in groups

    def test_an_unknown_kind_is_refused(self):
        with pytest.raises(Invalid):
            Operator("weird", "teleport")

    def test_an_empty_chain_is_refused(self):
        with pytest.raises(Invalid):
            fuse([])


class TestTheReport:
    def test_the_report_counts_removed_hops(self):
        report = fusion_report(chain())
        assert (
            "fused 5 operator(s) into 3 stage(s), 2 network "
            "hop(s) removed"
        ) in report
        assert (
            "[parse -> drop-nulls -> normalize] fused" in report
        )
        assert "by-user stands alone: it repartitions" in report

    def test_an_all_repartition_chain_removes_no_hops(self):
        allshuffle = [
            Operator("a", "keyby"),
            Operator("b", "shuffle"),
        ]
        report = fusion_report(allshuffle)
        assert "0 network hop(s) removed" in report
        assert "did nothing worth its complexity" in report

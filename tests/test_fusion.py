from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.fusion import Stage, fusion_verdict, plan_chain

PARSE = Stage(name="parse", ticks_per_event=3, ideal_workers=8)
CLEAN = Stage(name="clean", ticks_per_event=2, ideal_workers=8)
HEAVY_JOIN = Stage(
    name="join", ticks_per_event=20, ideal_workers=40
)
TINY_TAG = Stage(name="tag", ticks_per_event=1, ideal_workers=4)


class TestTheVerdict:
    def test_similar_widths_weld_without_waste(self):
        verdict = fusion_verdict(PARSE, CLEAN, events=1000)
        assert verdict.startswith("FUSE parse+clean")
        assert "saves 2000 hop tick(s)" in verdict

    def test_the_width_mismatch_keeps_the_hop(self):
        verdict = fusion_verdict(HEAVY_JOIN, TINY_TAG, events=1000)
        assert verdict.startswith("KEEP THE HOP join+tag")
        assert "90% of its slots idle" in verdict
        assert "this waste is bigger" in verdict

    def test_fusion_is_priced_against_actual_traffic(self):
        with pytest.raises(Invalid):
            fusion_verdict(PARSE, CLEAN, events=0)


class TestTheChain:
    def test_the_plan_interrogates_pair_by_pair(self):
        plan = plan_chain(
            [PARSE, CLEAN, HEAVY_JOIN, TINY_TAG], events=1000
        )
        assert "FUSE parse+clean" in plan
        assert "KEEP THE HOP join+tag" in plan
        assert "1 weld(s), 2 hop(s) kept" in plan
        assert "both defaults" in plan

    def test_a_chain_needs_length(self):
        with pytest.raises(Invalid):
            plan_chain([PARSE], events=10)

    def test_degenerate_stages_are_refused(self):
        with pytest.raises(Invalid):
            Stage(name="x", ticks_per_event=0, ideal_workers=1)

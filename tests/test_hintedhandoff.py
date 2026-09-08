from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.hintedhandoff import HintedHandoff


class TestDelivery:
    def test_a_reachable_target_is_delivered_not_hinted(self):
        handoff = HintedHandoff(hint_cap=5)
        assert handoff.write("r1", "v", reachable=True) == "delivered"
        assert handoff.pending("r1") == 0


class TestHinting:
    def test_an_unreachable_target_gets_a_hint(self):
        handoff = HintedHandoff(hint_cap=5)
        assert handoff.write("r1", "v1", reachable=False) == "hinted"
        assert handoff.pending("r1") == 1

    def test_recovery_replays_the_hints_in_order(self):
        handoff = HintedHandoff(hint_cap=5)
        handoff.write("r1", "a", reachable=False)
        handoff.write("r1", "b", reachable=False)
        assert handoff.recover("r1") == ["a", "b"]
        assert handoff.pending("r1") == 0


class TestCap:
    def test_hints_past_the_cap_are_dropped_and_flag_full_repair(self):
        handoff = HintedHandoff(hint_cap=2)
        handoff.write("r1", "a", reachable=False)
        handoff.write("r1", "b", reachable=False)
        verdict = handoff.write("r1", "c", reachable=False)
        assert "full repair needed" in verdict
        assert handoff.pending("r1") == 2
        assert handoff.dropped("r1") == 1
        assert handoff.needs_full_repair("r1")


class TestRefusals:
    def test_a_nonpositive_cap_is_refused(self):
        with pytest.raises(Invalid):
            HintedHandoff(hint_cap=0)

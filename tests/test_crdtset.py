from __future__ import annotations

import pytest

from rill.crdtset import GSet, TwoPhaseSet
from rill.errors import Invalid


class TestGSet:
    def test_it_accumulates_and_merges_by_union(self):
        left = GSet()
        left.add("a")
        right = GSet()
        right.add("b")
        left.merge(right)
        assert left.elements() == {"a", "b"}

    def test_the_merge_is_idempotent(self):
        left = GSet()
        left.add("a")
        right = GSet()
        right.add("a")
        left.merge(right)
        left.merge(right)
        assert left.elements() == {"a"}


class TestTwoPhaseSet:
    def test_add_then_remove_clears_the_element(self):
        s = TwoPhaseSet()
        s.add("x")
        assert s.contains("x")
        s.remove("x")
        assert not s.contains("x")

    def test_a_removed_element_can_never_be_re_added(self):
        s = TwoPhaseSet()
        s.add("x")
        s.remove("x")
        with pytest.raises(Invalid) as caught:
            s.add("x")
        assert "cannot re-add" in str(caught.value)

    def test_a_remove_wins_across_a_merge(self):
        left = TwoPhaseSet()
        left.add("x")
        right = TwoPhaseSet()
        right.merge(left)  # right now has x added
        left.remove("x")
        left.merge(right)
        right.merge(left)
        assert not left.contains("x")
        assert not right.contains("x")


class TestRefusals:
    def test_removing_a_never_added_element_is_refused(self):
        with pytest.raises(Invalid):
            TwoPhaseSet().remove("ghost")

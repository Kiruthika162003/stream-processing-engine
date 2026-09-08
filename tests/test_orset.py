from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.orset import ORSet


class TestBasics:
    def test_an_added_element_is_present(self):
        s = ORSet()
        s.add("x", "t1")
        assert s.contains("x")
        assert s.elements() == ["x"]

    def test_removing_the_observed_add_clears_the_element(self):
        s = ORSet()
        s.add("x", "t1")
        s.remove("x")
        assert not s.contains("x")


class TestAddWins:
    def test_a_concurrent_add_survives_a_remove_it_never_saw(self):
        alice = ORSet()
        alice.add("x", "t1")
        bob = ORSet()
        bob.merge(alice)  # bob sees the add tagged t1
        alice.remove("x")  # alice tombstones t1
        bob.add("x", "t2")  # bob re-adds with a fresh tag alice never saw
        alice.merge(bob)
        bob.merge(alice)
        assert alice.contains("x")
        assert bob.contains("x")

    def test_replicas_converge_regardless_of_merge_order(self):
        alice = ORSet()
        alice.add("x", "t1")
        bob = ORSet()
        bob.add("y", "t2")
        alice.merge(bob)
        bob.merge(alice)
        assert alice.elements() == bob.elements() == ["x", "y"]

    def test_a_readd_after_a_full_remove_brings_it_back(self):
        s = ORSet()
        s.add("x", "t1")
        s.remove("x")
        s.add("x", "t2")
        assert s.contains("x")


class TestRefusals:
    def test_an_empty_tag_is_refused(self):
        with pytest.raises(Invalid):
            ORSet().add("x", "")

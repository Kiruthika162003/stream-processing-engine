from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.lwwset import LwwSet


class TestResolution:
    def test_a_later_remove_wins_over_an_earlier_add(self):
        s = LwwSet()
        s.add("x", 1)
        s.remove("x", 5)
        assert not s.contains("x")

    def test_a_later_add_wins_over_an_earlier_remove(self):
        s = LwwSet()
        s.remove("x", 1)
        s.add("x", 5)
        assert s.contains("x")

    def test_a_tie_is_add_wins(self):
        s = LwwSet()
        s.add("x", 3)
        s.remove("x", 3)
        assert s.contains("x")

    def test_a_never_added_element_is_absent(self):
        s = LwwSet()
        s.remove("x", 1)
        assert not s.contains("x")


class TestMerge:
    def test_merge_takes_the_latest_of_each_timestamp(self):
        left = LwwSet()
        left.add("x", 2)
        right = LwwSet()
        right.remove("x", 5)  # a later remove elsewhere
        left.merge(right)
        assert not left.contains("x")

    def test_replicas_converge(self):
        left = LwwSet()
        left.add("x", 10)
        right = LwwSet()
        right.remove("x", 3)
        left.merge(right)
        right.merge(left)
        assert left.elements() == right.elements() == {"x"}


class TestRefusals:
    def test_a_negative_timestamp_is_refused(self):
        with pytest.raises(Invalid):
            LwwSet().add("x", -1)

from __future__ import annotations

import pytest

from rill.cuckoofilter import CuckooFilter
from rill.errors import Halted, Invalid


class TestMembership:
    def test_added_items_are_found_with_no_false_negatives(self):
        cf = CuckooFilter(buckets=64, slots=4)
        items = [f"item-{number}" for number in range(100)]
        for item in items:
            cf.add(item)
        assert all(cf.contains(item) for item in items)
        assert cf.load() == 100


class TestDeletion:
    def test_a_deleted_item_is_gone(self):
        cf = CuckooFilter(buckets=64, slots=4)
        cf.add("a")
        assert cf.delete("a")
        assert not cf.contains("a")

    def test_deleting_a_never_added_item_returns_false(self):
        cf = CuckooFilter(buckets=64, slots=4)
        assert not cf.delete("ghost")

    def test_deleting_one_leaves_the_others(self):
        cf = CuckooFilter(buckets=64, slots=4)
        for item in ("a", "b", "c"):
            cf.add(item)
        cf.delete("b")
        assert cf.contains("a")
        assert cf.contains("c")
        assert not cf.contains("b")


class TestLoadLimit:
    def test_insertion_fails_loudly_near_capacity(self):
        cf = CuckooFilter(buckets=8, slots=4, max_kicks=20)
        accepted = 0
        with pytest.raises(Halted):
            for number in range(1000):
                cf.add(f"x{number}")
                accepted += 1
        assert 28 <= accepted < 32


class TestRefusals:
    def test_a_non_power_of_two_bucket_count_is_refused(self):
        with pytest.raises(Invalid):
            CuckooFilter(buckets=10)

    def test_zero_slots_is_refused(self):
        with pytest.raises(Invalid):
            CuckooFilter(buckets=8, slots=0)

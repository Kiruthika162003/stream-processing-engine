from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.merkle import MerkleTree


def _filled(leaves: int) -> MerkleTree:
    tree = MerkleTree(leaves=leaves)
    for number in range(200):
        tree.put(f"k{number}", f"v{number}")
    return tree


class TestIdentical:
    def test_identical_trees_share_a_root_and_diff_in_one_compare(self):
        left, right = _filled(16), _filled(16)
        assert left.root() == right.root()
        differing, compared = left.diff(right)
        assert differing == []
        assert compared == 1


class TestDivergence:
    def test_one_changed_key_is_found_in_log_comparisons(self):
        left, right = _filled(16), _filled(16)
        right.put("k7", "CHANGED")
        differing, compared = left.diff(right)
        assert differing == [9]  # the bucket k7 hashes into
        assert compared == 9
        assert compared < left.leaves

    def test_a_new_key_shifts_only_its_bucket(self):
        left, right = _filled(16), _filled(16)
        right.put("brand-new-key", "v")
        differing, _ = left.diff(right)
        assert len(differing) == 1


class TestRefusals:
    def test_a_non_power_of_two_leaf_count_is_refused(self):
        with pytest.raises(Invalid):
            MerkleTree(leaves=10)

    def test_diffing_mismatched_shapes_is_refused(self):
        with pytest.raises(Invalid):
            MerkleTree(leaves=8).diff(MerkleTree(leaves=16))

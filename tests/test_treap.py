from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.treap import Treap


class TestOrderAndMembership:
    def test_inorder_traversal_is_sorted(self):
        rng = random.Random(29)
        treap = Treap(rng.random)
        keys = [5, 3, 8, 1, 9, 2, 7, 0, 4, 6]
        for k in keys:
            treap.insert(k)
        assert list(treap) == sorted(keys)

    def test_membership(self):
        rng = random.Random(1)
        treap = Treap(rng.random)
        for k in [5, 3, 8, 1, 9, 2]:
            treap.insert(k)
        assert 8 in treap
        assert 7 not in treap

    def test_duplicate_inserts_are_ignored(self):
        rng = random.Random(2)
        treap = Treap(rng.random)
        treap.insert(5)
        treap.insert(5)
        assert len(treap) == 1


class TestBalance:
    def test_sorted_inserts_stay_balanced(self):
        # sorted insertion is the worst case for a naive BST (height n);
        # the treap keeps height near log n despite it.
        rng = random.Random(29)
        for _ in range(50):
            treap = Treap(rng.random)
            n = 1000
            for k in range(n):
                treap.insert(k)
            assert list(treap) == list(range(n))
            assert len(treap) == n
            # measured average height was 22 for n=1000; a safe ceiling
            assert treap.height() < 60

    def test_the_heap_property_holds_at_every_node(self):
        rng = random.Random(7)
        treap = Treap(rng.random)
        for _ in range(2000):
            treap.insert(rng.randint(0, 5000))
        assert treap.heap_property_holds()


class TestRefusals:
    def test_a_missing_priority_source_is_refused(self):
        with pytest.raises(Invalid):
            Treap(None)

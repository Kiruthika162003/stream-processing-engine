from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.xortrie import XorTrie


class TestMaxXor:
    def test_a_concrete_query(self):
        t = XorTrie(bits=5)
        for x in [3, 10, 5, 25, 2, 8]:
            t.insert(x)
        # 25 ^ 5 == 28 is the largest partner for query 5
        assert t.max_xor(5) == max(5 ^ x for x in [3, 10, 5, 25, 2, 8])

    def test_it_matches_brute_over_random_sets(self):
        rng = random.Random(89)
        for _ in range(3000):
            nums = [rng.randint(0, 1023) for _ in range(rng.randint(1, 20))]
            t = XorTrie(bits=10)
            for x in nums:
                t.insert(x)
            q = rng.randint(0, 1023)
            assert t.max_xor(q) == max(q ^ x for x in nums)

    def test_maximum_xor_pair_in_a_set(self):
        nums = [3, 10, 5, 25, 2, 8]
        t = XorTrie(bits=5)
        t.insert(nums[0])
        best = 0
        for x in nums[1:]:
            best = max(best, t.max_xor(x))
            t.insert(x)
        brute = max(a ^ b for i, a in enumerate(nums) for b in nums[i + 1 :])
        assert best == brute == 28


class TestRefusals:
    def test_a_non_positive_width_is_refused(self):
        with pytest.raises(Invalid):
            XorTrie(bits=0)

    def test_querying_an_empty_trie_is_refused(self):
        with pytest.raises(Invalid):
            XorTrie(bits=8).max_xor(3)

    def test_an_oversized_value_is_refused(self):
        with pytest.raises(Invalid):
            XorTrie(bits=4).insert(9999)

    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            XorTrie(bits=4).insert(-1)

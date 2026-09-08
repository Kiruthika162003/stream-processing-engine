from __future__ import annotations

from collections import Counter

import pytest

from rill.errors import Invalid
from rill.jumphash import jump_hash

KEYS = [f"key-{number}" for number in range(6000)]


class TestBalance:
    def test_load_is_even_across_buckets(self):
        loads = Counter(jump_hash(key, 6) for key in KEYS)
        counts = [loads[i] for i in range(6)]
        assert max(counts) / (sum(counts) / 6) < 1.1

    def test_every_bucket_is_in_range(self):
        assert all(0 <= jump_hash(key, 6) < 6 for key in KEYS)


class TestMovement:
    def test_growing_the_bucket_count_moves_about_one_in_n(self):
        moved = sum(1 for key in KEYS if jump_hash(key, 6) != jump_hash(key, 7))
        # ideal for the seventh bucket is one in seven
        assert 0.12 < moved / len(KEYS) < 0.18


class TestDeterminism:
    def test_the_same_key_and_count_give_the_same_bucket(self):
        assert jump_hash("key-42", 10) == jump_hash("key-42", 10)


class TestRefusals:
    def test_a_nonpositive_bucket_count_is_refused(self):
        with pytest.raises(Invalid):
            jump_hash("key", 0)

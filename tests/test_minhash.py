from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.minhash import MinHash, similarity


def _build(items: list[str], num_hashes: int) -> MinHash:
    sketch = MinHash(num_hashes=num_hashes)
    for item in items:
        sketch.add(item)
    return sketch


class TestExtremes:
    def test_identical_sets_are_fully_similar(self):
        left = _build(["a", "b", "c"], 64)
        right = _build(["a", "b", "c"], 64)
        assert similarity(left, right) == 1.0

    def test_disjoint_sets_are_dissimilar(self):
        left = _build([f"x{n}" for n in range(100)], 64)
        right = _build([f"y{n}" for n in range(100)], 64)
        assert similarity(left, right) == 0.0


class TestEstimate:
    def test_it_estimates_a_known_jaccard(self):
        # 200-element sets overlapping in 100 of a 300 union: Jaccard 1/3
        left = _build([f"z{n}" for n in range(200)], 256)
        right = _build([f"z{n}" for n in range(100, 300)], 256)
        estimate = similarity(left, right)
        assert abs(estimate - 1 / 3) < 0.1

    def test_the_signature_is_the_hash_count_long(self):
        sketch = _build(["a"], 32)
        assert len(sketch.signature()) == 32


class TestRefusals:
    def test_a_nonpositive_hash_count_is_refused(self):
        with pytest.raises(Invalid):
            MinHash(num_hashes=0)

    def test_mismatched_signature_lengths_are_refused(self):
        with pytest.raises(Invalid):
            similarity(_build(["a"], 8), _build(["a"], 16))

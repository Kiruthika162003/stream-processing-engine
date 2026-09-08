from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.simhash import hamming_distance, simhash

DOC_A = {f"word{n}": 1 for n in range(100)}
DOC_B = {f"word{n}": 1 for n in range(5, 105)}  # shares 95 words with A
DOC_C = {f"other{n}": 1 for n in range(100)}  # disjoint from A


class TestSimilarity:
    def test_identical_documents_have_no_distance(self):
        assert hamming_distance(simhash(DOC_A), simhash(DOC_A)) == 0

    def test_similar_documents_differ_in_few_bits(self):
        assert hamming_distance(simhash(DOC_A), simhash(DOC_B)) < 15

    def test_different_documents_differ_in_many_bits(self):
        assert hamming_distance(simhash(DOC_A), simhash(DOC_C)) > 20

    def test_similar_is_much_closer_than_different(self):
        near = hamming_distance(simhash(DOC_A), simhash(DOC_B))
        far = hamming_distance(simhash(DOC_A), simhash(DOC_C))
        assert near < far


class TestRefusals:
    def test_no_features_is_refused(self):
        with pytest.raises(Invalid):
            simhash({})

    def test_a_negative_weight_is_refused(self):
        with pytest.raises(Invalid):
            simhash({"a": -1})

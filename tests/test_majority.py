from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.majority import candidate, majority


class TestMajorityExists:
    def test_it_finds_the_majority_element(self):
        assert majority([1, 1, 1, 2, 3]) == 1

    def test_a_bare_majority_counts(self):
        assert majority([9, 9, 9, 1, 1]) == 9


class TestNoMajority:
    def test_no_majority_returns_none(self):
        assert majority([1, 2, 3, 4]) is None

    def test_the_candidate_is_a_meaningless_artifact_without_a_majority(self):
        # the one-pass vote still names a candidate; only the verify
        # pass keeps it from being mistaken for a result
        chosen = candidate([1, 2, 3, 4])
        assert chosen in {1, 2, 3, 4}
        assert majority([1, 2, 3, 4]) is None

    def test_an_exact_tie_is_not_a_majority(self):
        assert majority([1, 1, 2, 2]) is None


class TestRefusals:
    def test_an_empty_stream_has_no_candidate(self):
        with pytest.raises(Invalid):
            candidate([])

    def test_an_empty_stream_has_no_majority(self):
        with pytest.raises(Invalid):
            majority([])

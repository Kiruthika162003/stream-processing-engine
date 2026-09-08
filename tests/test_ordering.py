from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.ordering import OrderChecker


class TestPerKeyOrder:
    def test_monotonic_per_key_sequences_pass(self):
        checker = OrderChecker()
        assert "in order" in checker.observe("a", 1)
        assert "in order" in checker.observe("a", 2)

    def test_cross_key_interleaving_is_not_disorder(self):
        checker = OrderChecker()
        checker.observe("a", 1)
        checker.observe("b", 1)
        checker.observe("a", 2)
        checker.observe("b", 2)
        verdict = checker.verdict()
        assert "per-key order held" in verdict
        assert "cross-key interleaving was correctly ignored" in (
            verdict
        )

    def test_the_backward_jump_names_the_partitioner(self):
        checker = OrderChecker()
        checker.observe("a", 5)
        verdict = checker.observe("a", 3)
        assert verdict.startswith("VIOLATION a: 3 <= 5")
        assert "look at the partitioner, not the whole timeline" in (
            verdict
        )
        assert len(checker.violations) == 1

    def test_negative_sequences_are_refused(self):
        with pytest.raises(Invalid):
            OrderChecker().observe("a", -1)


class TestTheVerdict:
    def test_the_cross_key_note_refuses_the_non_problem(self):
        checker = OrderChecker()
        checker.observe("a", 1)
        checker.observe("b", 1)
        note = checker.cross_key_note()
        assert "2 key(s) tracked" in note
        assert "debugs a non-problem for a week" in note

    def test_the_violation_verdict_blames_the_partitioner(self):
        checker = OrderChecker()
        checker.observe("a", 5)
        checker.observe("a", 3)
        verdict = checker.verdict()
        assert "1 per-key violation(s)" in verdict
        assert "not the timeline" in verdict

    def test_an_empty_checker_has_no_verdict(self):
        with pytest.raises(Invalid):
            OrderChecker().verdict()

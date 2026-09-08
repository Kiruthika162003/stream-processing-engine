from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.patternmatch import PatternMatcher


def fraud() -> PatternMatcher:
    return PatternMatcher(
        stages=("login", "password-change", "large-transfer"),
        window=60,
    )


class TestMatching:
    def test_the_full_sequence_completes(self):
        matcher = fraud()
        matcher.observe("user-1", "login", now=0)
        matcher.observe("user-1", "password-change", now=10)
        verdict = matcher.observe(
            "user-1", "large-transfer", now=20
        )
        assert "PATTERN COMPLETE" in verdict
        assert matcher.completed == ["user-1"]

    def test_out_of_sequence_events_are_ignored(self):
        matcher = fraud()
        matcher.observe("user-1", "login", now=0)
        verdict = matcher.observe(
            "user-1", "large-transfer", now=10
        )
        assert "out of sequence" in verdict

    def test_a_one_stage_pattern_is_a_filter(self):
        with pytest.raises(Invalid):
            PatternMatcher(stages=("only",), window=10)


class TestAbandonment:
    def test_a_stalled_pattern_is_abandoned_at_its_stage(self):
        matcher = fraud()
        matcher.observe("user-1", "login", now=0)
        matcher.observe("user-1", "password-change", now=10)
        verdict = matcher.observe(
            "user-1", "large-transfer", now=200
        )
        assert "died at stage 1 past the 60 budget" in verdict

    def test_the_diagnosis_names_the_deadly_stage(self):
        matcher = fraud()
        for user in range(3):
            matcher.observe(f"u{user}", "login", now=0)
            matcher.observe(
                f"u{user}", "password-change", now=200
            )
        diagnosis = matcher.diagnosis()
        assert "most die at stage 0 (login)" in diagnosis
        assert "invisible without counting deaths" in diagnosis

    def test_a_clean_run_has_nothing_to_diagnose(self):
        matcher = fraud()
        matcher.observe("user-1", "login", now=0)
        matcher.observe("user-1", "password-change", now=10)
        matcher.observe("user-1", "large-transfer", now=20)
        assert "none abandoned" in matcher.diagnosis()

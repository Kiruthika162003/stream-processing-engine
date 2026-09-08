from __future__ import annotations

import itertools

import pytest

from rill.determinism import DeterminismAudit
from rill.errors import Invalid


class TestTheAudit:
    def test_a_pure_operator_is_deterministic(self):
        audit = DeterminismAudit(
            operator=lambda events: "|".join(sorted(events))
        )
        assert "deterministic: identical input" in audit.verdict(
            ["b", "a", "c"]
        )

    def test_a_hidden_counter_is_caught(self):
        counter = itertools.count()

        def impure(events: list[str]) -> str:
            return f"{len(events)}-{next(counter)}"

        audit = DeterminismAudit(operator=impure)
        verdict = audit.verdict(["a", "b"])
        assert verdict.startswith("NON-DETERMINISTIC")
        assert "every exactly-once claim" in verdict

    def test_running_twice_returns_both_outputs(self):
        audit = DeterminismAudit(
            operator=lambda events: str(len(events))
        )
        first, second = audit.run_twice(["a", "b", "c"])
        assert first == second == "3"


class TestClassification:
    def test_each_suspect_names_its_fix(self):
        audit = DeterminismAudit(operator=lambda _e: "")
        assert "inject event time instead" in audit.classify(
            "time"
        )
        assert "seed from the event" in audit.classify("random")
        assert "sort first" in audit.classify("iteration")

    def test_an_unknown_suspect_is_refused(self):
        audit = DeterminismAudit(operator=lambda _e: "")
        with pytest.raises(Invalid):
            audit.classify("gremlins")

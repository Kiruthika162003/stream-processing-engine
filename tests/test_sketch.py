from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.sketch import CountMin


def loaded_sketch() -> tuple[CountMin, dict[str, int]]:
    sketch = CountMin(width=32, depth=3)
    truth = {}
    for number in range(40):
        key = f"key-{number}"
        weight = 1 + number % 5
        sketch.add(key, weight)
        truth[key] = weight
    return sketch, truth


class TestTheBargain:
    def test_answers_never_underestimate(self):
        sketch, truth = loaded_sketch()
        for key, true_count in truth.items():
            assert sketch.estimate(key) >= true_count

    def test_the_audit_found_the_improbable_not_the_impossible(self):
        sketch, truth = loaded_sketch()
        audit = sketch.overestimate_audit(truth)
        assert "IMPOSSIBLE" not in audit
        assert audit.startswith(
            "worst overestimate 7 on key-13, budget 3"
        )
        assert "cannot happen often" in audit

    def test_a_stranger_reads_as_collision_noise_only(self):
        sketch, _ = loaded_sketch()
        assert sketch.estimate("never-added") <= (
            sketch.error_budget() * 3
        )

    def test_thin_sketches_are_refused(self):
        with pytest.raises(Invalid):
            CountMin(width=1, depth=3)
        with pytest.raises(Invalid):
            CountMin(width=8, depth=0)


class TestTheAnswer:
    def test_the_answer_carries_its_budget(self):
        sketch, _ = loaded_sketch()
        line = sketch.answer("key-3")
        assert "at most" in line
        assert "budget" in line
        assert "reads as exact" in line

    def test_weightless_adds_are_refused(self):
        sketch, _ = loaded_sketch()
        with pytest.raises(Invalid):
            sketch.add("k", weight=0)

    def test_the_budget_is_weight_over_width(self):
        sketch = CountMin(width=10, depth=2)
        for _ in range(50):
            sketch.add("a")
        assert sketch.error_budget() == 5

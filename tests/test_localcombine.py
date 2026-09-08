from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.localcombine import LocalCombiner


class TestFolding:
    def test_sum_partials_accumulate_per_key(self):
        combiner = LocalCombiner(fold="sum")
        for _ in range(100):
            combiner.combine("hot", 1)
        assert combiner.emit() == {"hot": 100}

    def test_max_keeps_the_largest(self):
        combiner = LocalCombiner(fold="max")
        for value in (5, 12, 3, 9):
            combiner.combine("k", value)
        assert combiner.emit()["k"] == 12

    def test_the_non_associative_fold_is_refused(self):
        with pytest.raises(Invalid) as caught:
            LocalCombiner(fold="mean")
        assert "produces a wrong answer fast" in str(
            caught.value
        )


class TestTheSavings:
    def test_a_heavy_reduction_is_worth_it(self):
        combiner = LocalCombiner(fold="sum")
        for number in range(1000):
            combiner.combine(f"key-{number % 10}", 1)
        savings = combiner.savings()
        assert "1000 event(s) in, 10 partial(s) out" in savings
        assert "shuffle cut 99%" in savings
        assert "worth its complexity" in savings

    def test_a_thin_reduction_reconsiders_itself(self):
        combiner = LocalCombiner(fold="sum")
        for number in range(10):
            combiner.combine(f"unique-{number}", 1)
        savings = combiner.savings()
        assert "shuffle cut 0%" in savings
        assert "reconsider whether the combiner earns its place" in (
            savings
        )

    def test_an_empty_combiner_has_no_savings(self):
        with pytest.raises(Invalid):
            LocalCombiner(fold="sum").savings()

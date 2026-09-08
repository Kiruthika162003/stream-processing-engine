from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.localagg import Combiner, merge_partials


class TestTheGuard:
    def test_the_mean_is_refused_with_the_classic_bug(self):
        with pytest.raises(Invalid) as caught:
            Combiner(fold="mean")
        assert "every team writes exactly once" in str(
            caught.value
        )


class TestFolding:
    def test_hot_keys_collapse_beautifully(self):
        combiner = Combiner(fold="sum")
        for number in range(1000):
            combiner.add(
                "hot-a" if number % 2 else "hot-b", 1
            )
        shipped = combiner.flush()
        assert shipped == {"hot-a": 500, "hot-b": 500}
        bill = combiner.network_bill()
        assert "1000 event(s) became 2 message(s)" in bill
        assert "998 saved (99%)" in bill

    def test_unique_keys_get_the_honest_caveat(self):
        combiner = Combiner(fold="sum")
        for number in range(50):
            combiner.add(f"unique-{number}", 1)
        combiner.flush()
        bill = combiner.network_bill()
        assert "0 saved (0%)" in bill
        assert "plus the overhead of trying" in bill

    def test_count_and_max_fold_correctly(self):
        counter = Combiner(fold="count")
        for _ in range(3):
            counter.add("k", 99)
        assert counter.flush() == {"k": 3}
        maxer = Combiner(fold="max")
        for value in (4, 9, 2):
            maxer.add("k", value)
        assert maxer.flush() == {"k": 9}


class TestTheMerge:
    def test_partials_merge_to_the_same_answer(self):
        left = Combiner(fold="sum")
        right = Combiner(fold="sum")
        whole = Combiner(fold="sum")
        for number in range(10):
            value = number * 3
            (left if number % 2 else right).add("k", value)
            whole.add("k", value)
        merged = merge_partials(
            "sum", [left.flush(), right.flush()]
        )
        assert merged == whole.flush()

    def test_max_merges_by_max(self):
        merged = merge_partials(
            "max", [{"k": 7}, {"k": 12}, {"k": 3}]
        )
        assert merged == {"k": 12}

    def test_unmergeable_folds_are_refused(self):
        with pytest.raises(Invalid):
            merge_partials("mean", [{"k": 1}])

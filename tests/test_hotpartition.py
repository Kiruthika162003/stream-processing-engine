from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.hotpartition import HotSplitter


def splitter() -> HotSplitter:
    return HotSplitter(
        order_sensitive={"account-balance"}, fanout=4
    )


class TestTheSplit:
    def test_the_famous_key_spreads_across_sub_partitions(self):
        chosen = splitter()
        homes = {
            chosen.route("trending-hashtag", index)
            for index in range(20)
        }
        assert len(homes) == 4

    def test_the_ordered_key_refuses_to_split(self):
        chosen = splitter()
        with pytest.raises(Invalid) as caught:
            chosen.route("account-balance", 5)
        assert "reordering bug from a different door" in str(
            caught.value
        )

    def test_a_fanout_of_one_is_no_split(self):
        with pytest.raises(Invalid):
            HotSplitter(order_sensitive=set(), fanout=1)


class TestRecombine:
    def test_the_sub_aggregates_merge_back(self):
        chosen = splitter()
        for index in range(100):
            chosen.accumulate("trending", index, 1)
        assert chosen.recombine("trending", "sum") == 100

    def test_max_recombines_by_max(self):
        chosen = splitter()
        chosen.accumulate("peak", 0, 5)
        chosen.accumulate("peak", 1, 12)
        chosen.accumulate("peak", 2, 3)
        assert chosen.recombine("peak", "max") == 12

    def test_the_mean_cannot_recombine(self):
        chosen = splitter()
        chosen.accumulate("avg", 0, 5)
        with pytest.raises(Invalid) as caught:
            chosen.recombine("avg", "mean")
        assert "the split and the merge are one decision" in (
            str(caught.value)
        )


class TestBalance:
    def test_the_report_shows_the_spread(self):
        chosen = splitter()
        for index in range(100):
            chosen.accumulate("trending", index, 1)
        report = chosen.balance_report("trending")
        assert "spread across 4 sub-partition(s)" in report
        assert "no longer rides one partition" in report

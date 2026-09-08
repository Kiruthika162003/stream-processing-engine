from __future__ import annotations

import pytest

from rill.catchup import CatchupPlan
from rill.errors import Invalid


def outage_debt() -> CatchupPlan:
    return CatchupPlan(
        backlog=6000, arrival_rate=100, capacity=300
    )


class TestTheRows:
    def test_a_row_prices_both_costs(self):
        row = outage_debt().row(50)
        assert row == (
            "50%: caught up in 40 tick(s), live stays current"
        )

    def test_the_greedy_split_craters_live(self):
        row = outage_debt().row(75)
        assert "caught up in 27 tick(s)" in row
        assert "live lag grows 25 per tick" in row

    def test_the_timid_split_takes_longer(self):
        row = outage_debt().row(25)
        assert "caught up in 80 tick(s)" in row

    def test_the_split_is_strictly_between(self):
        with pytest.raises(Invalid):
            outage_debt().row(0)
        with pytest.raises(Invalid):
            outage_debt().row(100)


class TestTheFrontier:
    def test_the_frontier_prints_three_rows(self):
        frontier = outage_debt().frontier()
        assert "picks a row, not an adjective" in frontier
        assert frontier.count("caught up in") == 3

    def test_the_closed_kitchen_is_stated_as_such(self):
        starved = CatchupPlan(
            backlog=6000, arrival_rate=300, capacity=200
        )
        frontier = starved.frontier()
        assert "no split catches up" in frontier
        assert "a menu from a closed kitchen" in frontier

    def test_no_backlog_is_no_problem(self):
        with pytest.raises(Invalid):
            CatchupPlan(
                backlog=0, arrival_rate=10, capacity=20
            )

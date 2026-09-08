from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.rescale import (
    measure_move,
    moving_day_report,
    range_home,
    sticky_assignment,
    sticky_home,
)

KEYS = [f"user-{number}" for number in range(500)]


class TestTheThreeBills:
    def test_the_measured_ladder_holds(self):
        modulo, ranges, sticky = measure_move(KEYS, 4, 5)
        assert modulo.line() == (
            "modulo: 384 of 500 key(s) move (76%)"
        )
        assert ranges.line() == (
            "ranges: 246 of 500 key(s) move (49%)"
        )
        assert sticky.line() == (
            "sticky-groups: 106 of 500 key(s) move (21%)"
        )

    def test_the_report_prints_the_argument(self):
        report = moving_day_report(KEYS, 4, 5)
        assert report.startswith(
            "rescaling 4 -> 5 worker(s), a 25% capacity change:"
        )
        assert "plausibility dies" in report

    def test_no_keys_no_moving_day(self):
        with pytest.raises(Invalid):
            measure_move([], 4, 5)


class TestStickiness:
    def test_sticky_only_moves_groups_to_the_newcomer(self):
        before = sticky_assignment(4)
        after = sticky_assignment(5)
        movers = [
            group
            for group in before
            if before[group] != after[group]
        ]
        assert movers
        assert all(after[group] == 4 for group in movers)

    def test_the_assignment_is_deterministic(self):
        assert sticky_assignment(5) == sticky_assignment(5)
        assert sticky_home("user-1", 5) == sticky_home(
            "user-1", 5
        )

    def test_every_worker_holds_groups(self):
        assignment = sticky_assignment(5)
        holders = set(assignment.values())
        assert holders == {0, 1, 2, 3, 4}


class TestRefusals:
    def test_workerless_stages_are_refused(self):
        with pytest.raises(Invalid):
            range_home("k", 0)
        with pytest.raises(Invalid):
            sticky_assignment(0)

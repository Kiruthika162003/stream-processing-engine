from __future__ import annotations

import pytest

from rill.asof import AsOfJoin
from rill.errors import Invalid


def rates() -> AsOfJoin:
    join = AsOfJoin()
    join.publish(valid_from=100, value=150)
    join.publish(valid_from=200, value=155)
    join.publish(valid_from=300, value=148)
    return join


class TestTemporalCorrectness:
    def test_the_event_gets_the_version_current_then(self):
        verdict = rates().value_at(250)
        assert "value 155 (in effect since 200)" in verdict
        assert "not now" in verdict

    def test_a_boundary_event_gets_the_new_version(self):
        assert rates().enrich(200) == 155

    def test_the_event_after_the_last_version_holds_it(self):
        assert rates().enrich(999) == 148

    def test_versions_publish_in_time_order(self):
        join = rates()
        with pytest.raises(Invalid):
            join.publish(valid_from=150, value=999)


class TestThePrecedingEdge:
    def test_the_event_before_all_versions_has_no_reference(self):
        verdict = rates().value_at(50)
        assert "no reference at 50" in verdict
        assert "the backfill corruption" in verdict

    def test_enrich_returns_none_before_all_versions(self):
        assert rates().enrich(50) is None

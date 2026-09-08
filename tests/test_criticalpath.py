from __future__ import annotations

import pytest

from rill.criticalpath import critical_path
from rill.errors import Invalid

PREDS = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}
DUR = {"A": 2, "B": 5, "C": 1, "D": 3}


class TestCriticalPath:
    def test_it_finds_the_longest_dependency_chain(self):
        length, path = critical_path(PREDS, DUR)
        assert length == 10
        assert path == ["A", "B", "D"]

    def test_a_linear_chain_sums_its_durations(self):
        preds = {"X": [], "Y": ["X"], "Z": ["Y"]}
        dur = {"X": 3, "Y": 4, "Z": 5}
        assert critical_path(preds, dur)[0] == 12


class TestWhereEffortHelps:
    def test_speeding_an_off_path_stage_does_nothing(self):
        faster = {**DUR, "C": 0}
        assert critical_path(PREDS, faster)[0] == 10

    def test_speeding_an_on_path_stage_lowers_the_makespan(self):
        faster = {**DUR, "B": 2}
        assert critical_path(PREDS, faster)[0] == 7


class TestRefusals:
    def test_no_stages_is_refused(self):
        with pytest.raises(Invalid):
            critical_path({}, {})

    def test_a_cycle_is_refused(self):
        with pytest.raises(Invalid):
            critical_path({"A": ["B"], "B": ["A"]}, {"A": 1, "B": 1})

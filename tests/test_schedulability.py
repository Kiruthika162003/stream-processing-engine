from __future__ import annotations

import math

import pytest

from rill.errors import Invalid
from rill.schedulability import edf_schedulable, rm_bound, rm_schedulable


class TestBound:
    def test_a_single_task_bound_is_full_utilization(self):
        assert rm_bound(1) == 1.0

    def test_the_bound_falls_toward_ln_two(self):
        assert round(rm_bound(2), 4) == 0.8284
        assert rm_bound(100) < 0.70
        assert rm_bound(100) > math.log(2)


class TestTheGap:
    def test_a_set_between_the_bound_and_one_is_edf_only(self):
        utilizations = [0.45, 0.45]  # sum 0.9
        assert edf_schedulable(utilizations)
        assert not rm_schedulable(utilizations)

    def test_edf_fills_the_processor_to_the_brim(self):
        assert edf_schedulable([0.5, 0.5])
        assert not edf_schedulable([0.5, 0.51])

    def test_a_light_set_passes_both(self):
        utilizations = [0.3, 0.3]
        assert edf_schedulable(utilizations)
        assert rm_schedulable(utilizations)


class TestRefusals:
    def test_no_tasks_is_refused(self):
        with pytest.raises(Invalid):
            edf_schedulable([])

    def test_a_nonpositive_utilization_is_refused(self):
        with pytest.raises(Invalid):
            rm_schedulable([0.0])

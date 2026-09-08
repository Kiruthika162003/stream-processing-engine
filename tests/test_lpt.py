from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.lpt import lpt_makespan, naive_makespan


class TestLptWins:
    def test_big_job_first_beats_big_job_last(self):
        jobs = [1, 1, 1, 1, 1, 5]
        assert lpt_makespan(jobs, 2) == 5
        assert naive_makespan(jobs, 2) == 7

    def test_lpt_never_loses_to_naive_on_random_loads(self):
        rng = random.Random(1)
        jobs = [rng.randint(1, 20) for _ in range(30)]
        assert lpt_makespan(jobs, 4) <= naive_makespan(jobs, 4)


class TestLowerBounds:
    def test_the_makespan_is_at_least_the_largest_job(self):
        jobs = [10, 2, 3, 4]
        assert lpt_makespan(jobs, 3) >= max(jobs)

    def test_one_machine_runs_everything_in_series(self):
        assert lpt_makespan([3, 4, 5], 1) == 12


class TestRefusals:
    def test_zero_machines_is_refused(self):
        with pytest.raises(Invalid):
            lpt_makespan([1, 2], 0)

    def test_a_negative_job_is_refused(self):
        with pytest.raises(Invalid):
            lpt_makespan([-1], 2)

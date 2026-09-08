from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.saga import COMMITTED, COMPENSATED, Saga


class TestHappyPath:
    def test_all_steps_succeeding_commits_with_no_compensation(self):
        saga = Saga(steps=("charge", "ship", "notify"))
        run = saga.execute((True, True, True))
        assert run.status == COMMITTED
        assert run.completed == ("charge", "ship", "notify")
        assert run.compensated == ()
        assert run.failed_at is None


class TestCompensation:
    def test_a_failure_compensates_the_completed_prefix_in_reverse(self):
        saga = Saga(steps=("charge", "ship", "notify"))
        run = saga.execute((True, True, False))
        assert run.status == COMPENSATED
        assert run.completed == ("charge", "ship")
        assert run.compensated == ("ship", "charge")
        assert run.failed_at == "notify"

    def test_a_first_step_failure_compensates_nothing(self):
        saga = Saga(steps=("charge", "ship"))
        run = saga.execute((False, True))
        assert run.status == COMPENSATED
        assert run.completed == ()
        assert run.compensated == ()
        assert run.failed_at == "charge"

    def test_the_compensation_is_the_strict_reverse_of_completion(self):
        saga = Saga(steps=("a", "b", "c", "d"))
        run = saga.execute((True, True, True, False))
        assert run.compensated == tuple(reversed(run.completed))


class TestRefusals:
    def test_an_empty_saga_is_refused(self):
        with pytest.raises(Invalid):
            Saga(steps=())

    def test_a_mismatched_flag_count_is_refused(self):
        saga = Saga(steps=("a", "b"))
        with pytest.raises(Invalid):
            saga.execute((True,))

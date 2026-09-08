from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.priorityinherit import PriorityLock


class TestInversion:
    def test_without_inheritance_a_medium_task_preempts_the_low_holder(self):
        lock = PriorityLock(inherit=False)
        lock.acquire("low", 1)
        lock.acquire("high", 10)  # high waits on the lock
        assert lock.holder_effective_priority() == 1
        assert lock.can_preempt(5)  # a medium task preempts the low holder

    def test_with_inheritance_the_holder_borrows_the_waiter_priority(self):
        lock = PriorityLock(inherit=True)
        lock.acquire("low", 1)
        lock.acquire("high", 10)
        assert lock.holder_effective_priority() == 10
        assert not lock.can_preempt(5)  # medium can no longer preempt


class TestHandoff:
    def test_release_hands_the_lock_to_the_highest_waiter(self):
        lock = PriorityLock()
        lock.acquire("low", 1)
        lock.acquire("mid", 5)
        lock.acquire("high", 10)
        lock.release()
        assert lock.holder_effective_priority() == 10  # high took it

    def test_release_of_the_last_holder_frees_the_lock(self):
        lock = PriorityLock()
        lock.acquire("only", 3)
        lock.release()
        with pytest.raises(Invalid):
            lock.holder_effective_priority()


class TestRefusals:
    def test_releasing_a_free_lock_is_refused(self):
        with pytest.raises(Invalid):
            PriorityLock().release()

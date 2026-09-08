from __future__ import annotations

import pytest

from rill.deadlock import WaitForGraph
from rill.errors import Invalid


class TestDetection:
    def test_a_cycle_is_a_deadlock(self):
        graph = WaitForGraph()
        graph.wait("T1", "T2")
        graph.wait("T2", "T3")
        graph.wait("T3", "T1")
        assert graph.deadlocked()
        assert set(graph.find_cycle()) == {"T1", "T2", "T3"}

    def test_a_chain_reaching_a_running_txn_is_not_a_deadlock(self):
        graph = WaitForGraph()
        graph.wait("T1", "T2")
        graph.wait("T2", "T3")  # T3 is running, not waiting
        assert not graph.deadlocked()

    def test_the_victim_is_on_the_cycle(self):
        graph = WaitForGraph()
        graph.wait("T1", "T2")
        graph.wait("T2", "T1")
        assert graph.victim() in {"T1", "T2"}


class TestResolution:
    def test_resolving_a_wait_breaks_the_cycle(self):
        graph = WaitForGraph()
        graph.wait("T1", "T2")
        graph.wait("T2", "T1")
        assert graph.deadlocked()
        graph.resolve("T2", "T1")
        assert not graph.deadlocked()


class TestRefusals:
    def test_a_self_wait_is_refused(self):
        with pytest.raises(Invalid):
            WaitForGraph().wait("T1", "T1")

    def test_a_victim_without_a_deadlock_is_refused(self):
        graph = WaitForGraph()
        graph.wait("T1", "T2")
        with pytest.raises(Invalid):
            graph.victim()

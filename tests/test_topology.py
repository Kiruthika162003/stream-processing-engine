from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.topology import Topology


def wired_job() -> Topology:
    job = Topology()
    job.add_stage("ingest", parallelism=4, source=True)
    job.add_stage("clean", parallelism=2)
    job.add_stage("aggregate", parallelism=8)
    job.add_stage("emit", parallelism=1, sink=True)
    job.wire("ingest", "clean")
    job.wire("clean", "aggregate")
    job.wire("aggregate", "emit")
    return job


class TestWiring:
    def test_a_cycle_is_refused_with_the_loop_spelled_out(self):
        job = wired_job()
        with pytest.raises(Invalid) as caught:
            job.wire("aggregate", "clean")
        message = str(caught.value)
        assert "closes the loop" in message
        assert "aggregate -> clean -> aggregate" in message
        assert "metrics look busy" in message

    def test_stages_wire_once(self):
        job = wired_job()
        with pytest.raises(Invalid):
            job.add_stage("clean")

    def test_workerless_stages_are_refused(self):
        with pytest.raises(Invalid):
            Topology().add_stage("x", parallelism=0)


class TestTheReview:
    def test_a_healthy_graph_is_fed_and_heard(self):
        assert wired_job().wiring_review() == (
            "4 stage(s) wired, every one fed and heard"
        )

    def test_the_silent_stage_is_named(self):
        job = wired_job()
        job.add_stage("orphan", parallelism=2)
        job.wire("orphan", "emit")
        review = job.wiring_review()
        assert (
            "orphan: no source reaches it; it will run as "
            "silence"
        ) in review

    def test_the_unheard_stage_is_named(self):
        job = wired_job()
        job.add_stage("vanity-metrics", parallelism=1)
        job.wire("clean", "vanity-metrics")
        review = job.wiring_review()
        assert (
            "vanity-metrics: reaches no sink; it will run as "
            "cost"
        ) in review

    def test_a_sourceless_topology_means_nothing(self):
        job = Topology()
        job.add_stage("only", sink=True)
        with pytest.raises(Invalid):
            job.wiring_review()


class TestTheSlotBill:
    def test_the_bill_speaks_the_schedulers_language(self):
        bill = wired_job().slot_bill()
        assert bill.startswith(
            "15 slot(s) across 4 stage(s); aggregate is "
            "widest at 8"
        )

from __future__ import annotations

import pytest

from rill.dlq import DeadLetterRouter
from rill.errors import Invalid


def router() -> DeadLetterRouter:
    return DeadLetterRouter(max_retries=3)


class TestRouting:
    def test_transient_failures_retry_within_budget(self):
        chosen = router()
        verdict = chosen.fail("evt-1", "connection reset")
        assert "retry 1/3; transient until proven poison" in (
            verdict
        )

    def test_the_poison_event_lands_in_the_dlq(self):
        chosen = router()
        for _ in range(4):
            verdict = chosen.fail("evt-1", "unparseable payload")
        assert "to the DLQ after 4 attempt(s)" in verdict
        assert "a workbench entry, not a silent drop" in verdict
        assert "evt-1" in chosen.dead_letters

    def test_a_reasonless_failure_cannot_be_triaged(self):
        with pytest.raises(Invalid):
            router().fail("evt-1", "  ")

    def test_a_negative_budget_is_refused(self):
        with pytest.raises(Invalid):
            DeadLetterRouter(max_retries=-1)


class TestReplay:
    def test_a_fixed_event_replays_out_of_the_dlq(self):
        chosen = router()
        for _ in range(4):
            chosen.fail("evt-1", "bad schema")
        verdict = chosen.replay("evt-1")
        assert "replayed after a human fixed the cause" in (
            verdict
        )
        assert "evt-1" not in chosen.dead_letters

    def test_replaying_a_stranger_is_refused(self):
        with pytest.raises(Invalid):
            router().replay("ghost")


class TestHealth:
    def test_the_empty_dlq_is_healthy(self):
        assert router().health(oldest_age=0, sla=100) == (
            "DLQ empty; every event found a home"
        )

    def test_the_sla_breach_is_named(self):
        chosen = router()
        for _ in range(4):
            chosen.fail("evt-1", "poison")
        health = chosen.health(oldest_age=500, sla=100)
        assert "oldest entry 500 past the 100 SLA" in health
        assert "a bug nobody is fixing" in health

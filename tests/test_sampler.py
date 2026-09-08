from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.sampler import (
    TailSampler,
    consistency_check,
    head_decision,
)


class TestHeadSampling:
    def test_the_decision_is_deterministic_per_trace(self):
        for trace in (f"trace-{n}" for n in range(50)):
            assert head_decision(trace, 10) == head_decision(
                trace, 10
            )

    def test_a_wider_rate_keeps_a_superset(self):
        traces = [f"t-{n}" for n in range(200)]
        narrow = {t for t in traces if head_decision(t, 10)}
        wide = {t for t in traces if head_decision(t, 50)}
        assert narrow <= wide

    def test_bad_rates_are_refused(self):
        with pytest.raises(Invalid):
            head_decision("t", 150)


class TestConsistency:
    def test_every_stage_agrees_on_the_same_trace(self):
        verdict = consistency_check("trace-7", 10, stages=5)
        assert "consistent, because a partial trace is worse" in (
            verdict
        )
        assert "whole" in verdict


class TestTailSampling:
    def test_the_error_trace_is_kept(self):
        sampler = TailSampler()
        sampler.observe("t-1", is_error=False)
        sampler.observe("t-1", is_error=True)
        verdict = sampler.decide("t-1")
        assert "kept: an error trace" in verdict
        assert "head sampling would have dropped" in verdict

    def test_the_boring_trace_is_dropped_at_the_tail(self):
        sampler = TailSampler()
        sampler.observe("t-2", is_error=False)
        assert "dropped: boring, decided at the tail" in (
            sampler.decide("t-2")
        )

    def test_an_unbuffered_trace_cannot_be_decided(self):
        with pytest.raises(Invalid):
            TailSampler().decide("ghost")

    def test_the_buffer_cost_is_named(self):
        sampler = TailSampler()
        for number in range(5):
            sampler.observe(f"t-{number}", is_error=False)
        sampler.decide("t-0")
        cost = sampler.buffer_cost()
        assert "4 trace(s) buffered awaiting verdict" in cost
        assert "it is not free" in cost

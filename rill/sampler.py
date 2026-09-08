"""Consistent sampling: the same trace, whole, across every stage or none.

Sampling one event in a thousand for a trace is easy; sampling
consistently is the hard part nobody plans for, because if
each stage independently decides to sample, a trace is kept at
stage one and dropped at stage two, and the partial trace that
results is worse than no trace, a story missing its middle
that leads the debugger to a wrong conclusion. The consistent
sampler decides once, at the trace's root, by hashing the
trace id against the sample rate, and every downstream stage
re-derives the same decision from the same id, so a trace is
sampled whole or not at all. The head-versus-tail choice is
made explicit: head sampling decides at ingress cheaply but
blindly, keeping boring traces and dropping the error that
had not happened yet, while tail sampling buffers and decides
at the end, keeping the interesting traces at the cost of
holding them all until the verdict, and the module prices the
buffer that tail sampling's superiority actually costs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_bucket
from rill.errors import Invalid


def head_decision(trace_id: str, sample_percent: int) -> bool:
    if not 0 <= sample_percent <= 100:
        raise Invalid("the sample rate is a percentage")
    return stable_bucket(trace_id, 100) < sample_percent


@dataclass
class TailSampler:
    buffer: dict[str, list[str]] = field(default_factory=dict)
    kept: list[str] = field(default_factory=list)
    dropped: int = 0

    def observe(self, trace_id: str, is_error: bool) -> None:
        self.buffer.setdefault(trace_id, [])
        if is_error:
            self.buffer[trace_id].append("error")

    def decide(self, trace_id: str) -> str:
        spans = self.buffer.pop(trace_id, None)
        if spans is None:
            raise Invalid(f"{trace_id} was never buffered")
        if "error" in spans:
            self.kept.append(trace_id)
            return (
                f"{trace_id} kept: an error trace, the one tail "
                "sampling exists to catch that head sampling "
                "would have dropped"
            )
        self.dropped += 1
        return f"{trace_id} dropped: boring, decided at the tail"

    def buffer_cost(self) -> str:
        held = len(self.buffer)
        return (
            f"{held} trace(s) buffered awaiting verdict, "
            f"{len(self.kept)} kept, {self.dropped} dropped; "
            "the buffer is what tail sampling's superiority "
            "costs, and it is not free"
        )


def consistency_check(
    trace_id: str, sample_percent: int, stages: int
) -> str:
    decisions = {
        head_decision(trace_id, sample_percent)
        for _ in range(stages)
    }
    if len(decisions) == 1:
        verdict = "sampled whole" if decisions.pop() else "dropped whole"
        return (
            f"{trace_id} across {stages} stage(s): {verdict}; "
            "consistent, because a partial trace is worse than "
            "none"
        )
    return f"{trace_id}: INCONSISTENT, the failure mode to prevent"

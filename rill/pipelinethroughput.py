"""Pipeline throughput: the slowest stage sets the rate, and only speeding it up helps.

A pipeline of stages in series can process events no faster than
its slowest stage, because every event must pass through every
stage and the slow one backs up while the fast ones idle waiting
for it. So the pipeline's throughput is the minimum of the stage
rates, not their average and not the sum, and the practical
consequence is the same one the max-flow min-cut and the queueing
curve keep repeating in different clothes: optimizing anywhere but
the bottleneck is wasted effort. Doubling the rate of a stage that
was already faster than the slowest changes nothing, because that
stage was never the constraint; doubling the slowest stage lifts
the whole pipeline's throughput up to wherever the next-slowest
stage now sits, at which point that stage becomes the new
bottleneck and the effort must move there. Performance work on a
pipeline is therefore a sequence of finding the current bottleneck
and relieving it, one stage at a time, and profiling that does not
identify the bottleneck first is guessing. This module reports the
throughput, names the bottleneck stage, and computes what speeding
a given stage would yield, so the min-rule and the futility of
optimizing off the bottleneck are measured numbers rather than a
principle stated and then ignored under deadline.
"""

from __future__ import annotations

from rill.errors import Invalid


def throughput(stage_rates: list[int]) -> int:
    if not stage_rates:
        raise Invalid("a pipeline needs at least one stage")
    if any(rate <= 0 for rate in stage_rates):
        raise Invalid("stage rates must be positive")
    return min(stage_rates)


def bottleneck_stage(stage_rates: list[int]) -> int:
    if not stage_rates:
        raise Invalid("a pipeline needs at least one stage")
    return min(range(len(stage_rates)), key=lambda i: stage_rates[i])


def throughput_after(stage_rates: list[int], stage: int, new_rate: int) -> int:
    if not 0 <= stage < len(stage_rates):
        raise Invalid("stage index out of range")
    if new_rate <= 0:
        raise Invalid("the new rate must be positive")
    adjusted = list(stage_rates)
    adjusted[stage] = new_rate
    return throughput(adjusted)

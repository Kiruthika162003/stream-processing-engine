"""Adaptive sampling: hold the sampled volume steady by moving the rate as the input moves.

Sampling a stream at a fixed probability produces an output whose
volume tracks the input's, which is exactly wrong when the point
of sampling is to cap the volume. At ten percent, a quiet period
of a hundred events a second yields ten samples and a burst of ten
thousand yields a thousand, so the very moment the pipeline is
most loaded is when the sampler dumps the most on it, and the
quiet moment when there is capacity to spare is when it samples
almost nothing. Adaptive sampling inverts the knob: instead of
fixing the probability, fix the target output rate and derive the
probability from the observed input rate as the target over the
input, capped at one. Now a burst that is ten times the input
gets sampled at a tenth the probability and yields the same target
volume, while a quiet period samples nearly everything and still
only reaches the target, so the output holds near the target
regardless of how the input swings. The cost is that the sample is
no longer a fixed fraction of the stream, so it cannot be used to
estimate absolute counts without dividing back out by the rate
that was in force. This module computes the adaptive probability
and the expected output, so the steady volume it holds against a
swinging input is a measured quantity.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class AdaptiveSampler:
    target_rate: int

    def __post_init__(self) -> None:
        if self.target_rate <= 0:
            raise Invalid("target rate must be positive")

    def probability(self, observed_rate: int) -> float:
        if observed_rate < 0:
            raise Invalid("observed rate cannot be negative")
        if observed_rate == 0:
            return 1.0
        return min(1.0, self.target_rate / observed_rate)

    def expected_output(self, observed_rate: int) -> float:
        return self.probability(observed_rate) * observed_rate

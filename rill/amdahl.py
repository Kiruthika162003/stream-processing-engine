"""Amdahl versus Gustafson: the same serial fraction, two opposite verdicts on scaling.

Two laws predict speedup from parallelism and reach opposite
conclusions from the same serial fraction, because they ask
different questions. Amdahl fixes the workload and asks how much
faster it finishes on more cores: the serial part does not shrink,
so speedup is one over the serial fraction plus the parallel
fraction divided by cores, and it is capped at one over the serial
fraction no matter how many cores you add. A tenth serial means a
ceiling of ten times, and a thousand cores buys almost nothing past
that. Gustafson fixes the time and asks how much more work more
cores can do: the parallel part grows to fill the added capacity
while the serial part stays constant, so scaled speedup is the
serial fraction plus the parallel fraction times cores, which is
near linear. The contradiction is only apparent. Amdahl answers a
fixed problem run faster, the right question for a latency-bound
job, and Gustafson answers a bigger problem in the same time, the
right question for a throughput-bound one, and quoting the wrong
law for the situation is how a scaling argument goes wrong. This
module computes both, so the fixed-problem ceiling and the
scaled-problem near-linear growth are measured side by side.
"""

from __future__ import annotations

from rill.errors import Invalid


def _validate(parallel_fraction: float, cores: int) -> None:
    if not 0.0 <= parallel_fraction <= 1.0:
        raise Invalid("parallel fraction is in [0, 1]")
    if cores < 1:
        raise Invalid("cores must be positive")


def amdahl_speedup(parallel_fraction: float, cores: int) -> float:
    _validate(parallel_fraction, cores)
    serial = 1 - parallel_fraction
    return 1 / (serial + parallel_fraction / cores)


def amdahl_ceiling(parallel_fraction: float) -> float:
    if not 0.0 <= parallel_fraction < 1.0:
        raise Invalid("ceiling is undefined at a fully parallel workload")
    return 1 / (1 - parallel_fraction)


def gustafson_speedup(parallel_fraction: float, cores: int) -> float:
    _validate(parallel_fraction, cores)
    return (1 - parallel_fraction) + parallel_fraction * cores

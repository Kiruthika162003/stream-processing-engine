"""Universal Scalability Law: more workers help, then a coherency cost makes them hurt.

Adding workers to a pipeline does not scale throughput linearly,
and the Universal Scalability Law says why with two penalties.
Contention, the fraction of work that must serialize on a shared
resource, bends the curve so that N workers deliver less than N
times the throughput, the same ceiling Amdahl describes. Coherency,
the cost of keeping the workers consistent with each other, is
worse, because it grows with the number of pairs of workers, so it
scales with N squared, and past some point each added worker
spends more on staying coherent than it contributes in work. When
coherency is present at all the throughput curve does not merely
flatten, it peaks and then falls, the retrograde region where a
bigger cluster is slower than a smaller one, and the peak sits at
the square root of one minus contention over coherency. Ignore the
coherency term and the law degrades to Amdahl, a curve that
plateaus but never declines, which is why a system that gets
slower as you add machines is diagnosed by a nonzero coherency
coefficient. This module computes the throughput curve and the
retrograde peak, so the point where more workers start to hurt is
a number and not a war story.
"""

from __future__ import annotations

import math

from rill.errors import Invalid


def throughput(workers: int, contention: float, coherency: float) -> float:
    if workers < 1:
        raise Invalid("need at least one worker")
    if contention < 0 or coherency < 0:
        raise Invalid("coefficients cannot be negative")
    denominator = 1 + contention * (workers - 1) + coherency * workers * (workers - 1)
    return workers / denominator


def peak_workers(contention: float, coherency: float) -> float:
    if coherency <= 0:
        raise Invalid("without coherency the curve never peaks; this is Amdahl")
    if not 0 <= contention <= 1:
        raise Invalid("contention is a fraction in [0, 1]")
    return math.sqrt((1 - contention) / coherency)

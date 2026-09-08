"""Outlier detection: the mean-and-sigma test hides the very outliers that break it.

Flagging anomalous values by how many standard deviations they
sit from the mean is the reflexive method and it has a hole the
outliers themselves dig. A handful of extreme values pulls the
mean toward them and inflates the standard deviation far more,
because the deviation squares the distance, so the threshold of
three sigma stretches out to swallow the very points it was meant
to catch: the outliers hide inside a spread they created. This is
masking, and it gets worse the more extreme the outlier is. The
robust alternative measures spread with the median absolute
deviation, the median of the distances from the median, which a
few wild values cannot move because the median ignores them. A
modified z-score built on the median and the MAD flags the
outliers the mean-based test masks, because neither its center
nor its scale was contaminated by them. The tradeoff is that MAD
assumes a roughly symmetric bulk and costs a sort for the medians,
where the mean and sigma are a single pass, so the mean test
survives on clean data and fails exactly when it matters. This
module computes both scores so the masking is a measured
disagreement: the same point the sigma test calls normal the MAD
test calls an outlier.
"""

from __future__ import annotations

import statistics

from rill.errors import Invalid


def zscore_outliers(values: list[float], threshold: float = 3.0) -> list[float]:
    if len(values) < 2:
        raise Invalid("need at least two values")
    mean = statistics.fmean(values)
    stdev = statistics.pstdev(values)
    if stdev == 0:
        return []
    return [x for x in values if abs(x - mean) / stdev > threshold]


def mad_outliers(values: list[float], threshold: float = 3.0) -> list[float]:
    if len(values) < 2:
        raise Invalid("need at least two values")
    median = statistics.median(values)
    deviations = [abs(x - median) for x in values]
    mad = statistics.median(deviations)
    if mad == 0:
        return []
    return [x for x in values if 0.6745 * abs(x - median) / mad > threshold]

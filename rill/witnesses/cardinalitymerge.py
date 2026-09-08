"""Two shards estimate distinct users, and the merge matches the true union.

The drill builds two cardinality estimators over overlapping
key ranges, shard A seeing users 0 through 499 and shard B
seeing 250 through 749, whose true union is 750 distinct
users, and merges them without either shard re-reading its
data. The merged estimate is checked against the true 750
within the estimator's error band, which is the property that
makes the approximation worth its inexactness: a distinct
count across a fleet is the merge of per-node estimates, an
operation an exact counter cannot perform without shipping
every value to one node. The deposition also pins the
small-range correction that the module's own docstring
records as a fixed bug, confirming that a single distinct
value estimates one and not the dozens the uncorrected
harmonic mean produced, because a cardinality estimator that
is wrong at one is untrustworthy at a million.
"""

from __future__ import annotations

from rill.hyperloglog import CardinalityEstimator
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    shard_a = CardinalityEstimator()
    shard_b = CardinalityEstimator()
    for number in range(500):
        shard_a.observe(f"user-{number}")
    for number in range(250, 750):
        shard_b.observe(f"user-{number}")
    merged = shard_a.merge(shard_b)
    merged_estimate = merged.estimate()
    single = CardinalityEstimator()
    for _ in range(1000):
        single.observe("one-user")
    numbers = {
        "true_union": 750,
        "merged_estimate": merged_estimate,
        "merged_error_percent": round(
            100 * abs(merged_estimate - 750) / 750
        ),
        "single_distinct_estimate": single.estimate(),
    }
    holds = (
        650 < merged_estimate < 850
        and single.estimate() <= 2
    )
    return Deposition(
        witness="cardinalitymerge",
        claim=(
            "two shards merge into a union estimate near the "
            "true 750 without re-reading data, and the "
            "small-range correction holds one distinct at one, "
            "not the dozens the uncorrected mean gave"
        ),
        numbers=numbers,
        holds=holds,
    )

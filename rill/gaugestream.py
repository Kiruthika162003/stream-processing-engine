"""Gauges versus counters: two metric shapes that aggregate in opposite ways.

Streaming metrics come in two shapes that beginners aggregate
identically and wrongly: a counter only goes up and aggregates
by summing, total requests across shards is the sum of each
shard's count, while a gauge is a point-in-time value and
aggregates by averaging or taking the latest, current memory
across shards is not the sum of each shard's memory, it is
their sum only if you want total and their average if you want
typical. Summing a gauge that should be averaged produces a
number that grows with the shard count for no real reason, the
classic dashboard that shows memory usage climbing every time
you add a replica. The module tags each metric with its shape
and refuses to aggregate a gauge by summing when the query
wants a representative value, because the aggregation that fits
a counter corrupts a gauge, and the corruption is invisible
until someone notices the metric scales with the fleet size
instead of the load.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

SHAPES = ("counter", "gauge")


@dataclass(frozen=True)
class Metric:
    name: str
    shape: str

    def __post_init__(self) -> None:
        if self.shape not in SHAPES:
            raise Invalid(f"{self.name}: shape is one of {SHAPES}")


def aggregate(
    metric: Metric, values: list[int], how: str
) -> str:
    if not values:
        raise Invalid("nothing to aggregate")
    if metric.shape == "counter":
        if how != "sum":
            raise Invalid(
                f"{metric.name} is a counter; averaging it "
                "loses the total it exists to report"
            )
        return f"{metric.name} total: {sum(values)}"
    if how == "sum":
        raise Invalid(
            f"{metric.name} is a gauge; summing it makes a "
            "number that grows with shard count for no reason, "
            "the dashboard that climbs every time you add a "
            "replica"
        )
    if how == "average":
        return (
            f"{metric.name} typical: "
            f"{sum(values) // len(values)} (averaged, the "
            "representative value)"
        )
    if how == "latest":
        return f"{metric.name} latest: {values[-1]}"
    raise Invalid(f"unknown aggregation {how}")

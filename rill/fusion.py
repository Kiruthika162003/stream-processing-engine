"""Operator fusion: chained operators that never touch the network.

A map followed by a filter followed by another map is three
operators, and if each runs on a separate node the events
serialize and cross the network twice between them for no
reason, since none of the three repartitions the data. Fusion
collapses a chain of operators that preserve partitioning into
one fused operator that runs on a single node, so the events
flow through as method calls instead of network messages. The
rule that governs what may fuse is whether an operator keeps
the data on the same partition, a map and a filter do, a
keyed aggregation and a shuffle do not, and fusing across a
repartition would silently move data to the wrong node. The
planner walks a chain and fuses maximal runs of
partition-preserving operators, reporting the network hops
removed, because the whole value is the hop count that went
from many to few, and a fusion that removed no hops fused
operators that were already on one node and did nothing worth
the complexity.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

PRESERVING = ("map", "filter", "flatmap")
REPARTITIONING = ("keyby", "shuffle", "aggregate")


@dataclass(frozen=True)
class Operator:
    name: str
    kind: str

    def __post_init__(self) -> None:
        if self.kind not in PRESERVING + REPARTITIONING:
            raise Invalid(
                f"{self.name}: unknown operator kind {self.kind}"
            )

    def preserves_partition(self) -> bool:
        return self.kind in PRESERVING


def fuse(chain: list[Operator]) -> list[list[str]]:
    if not chain:
        raise Invalid("an empty chain fuses nothing")
    groups: list[list[str]] = []
    current: list[str] = []
    for operator in chain:
        if operator.preserves_partition():
            current.append(operator.name)
        else:
            if current:
                groups.append(current)
                current = []
            groups.append([operator.name])
    if current:
        groups.append(current)
    return groups


def fusion_report(chain: list[Operator]) -> str:
    groups = fuse(chain)
    hops_before = len(chain) - 1
    hops_after = len(groups) - 1
    removed = hops_before - hops_after
    lines = [
        f"fused {len(chain)} operator(s) into {len(groups)} "
        f"stage(s), {removed} network hop(s) removed"
    ]
    for group in groups:
        if len(group) > 1:
            lines.append(
                f"  [{' -> '.join(group)}] fused, one node, "
                "method calls not messages"
            )
        else:
            lines.append(
                f"  {group[0]} stands alone: it repartitions"
            )
    if removed == 0:
        lines.append(
            "no hops removed: these operators already shared a "
            "node, and the fusion did nothing worth its "
            "complexity"
        )
    return "\n".join(lines)

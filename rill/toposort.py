"""Kahn's topological sort: an order where every stage follows its dependencies.

Scheduling stages that depend on one another needs an order in
which no stage runs before something it needs, which exists
exactly when the dependency graph has no cycle. Kahn's algorithm
builds that order by peeling: count each stage's incoming
dependencies, start with the ones that have none, and repeatedly
emit a dependency-free stage and remove it, which lowers the
incoming count of everything that depended on it and may free more
stages to emit next. When the graph is acyclic every stage
eventually reaches a zero count and is emitted, and the order they
come out in is a valid schedule. The cycle case falls out for
free: if a cycle exists, its stages depend on each other in a loop
so none of them ever reaches zero incoming, and the algorithm
emits fewer stages than the graph holds, which is the signal that
no valid order exists. So the same peel both produces the schedule
and detects the impossibility. This module returns a topological
order, breaking ties by name so the order is deterministic, and
refuses a cyclic graph by noticing the count of emitted stages
falls short, so a runnable order is a result and an unrunnable
graph is a named failure.
"""

from __future__ import annotations

import heapq

from rill.errors import Invalid


def topological_order(
    nodes: list[str], edges: list[tuple[str, str]]
) -> list[str]:
    indegree = dict.fromkeys(nodes, 0)
    successors: dict[str, list[str]] = {node: [] for node in nodes}
    for before, after in edges:
        if before not in indegree or after not in indegree:
            raise Invalid("an edge names a stage not in the node set")
        successors[before].append(after)
        indegree[after] += 1
    ready = [node for node in nodes if indegree[node] == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        node = heapq.heappop(ready)
        order.append(node)
        for successor in successors[node]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                heapq.heappush(ready, successor)
    if len(order) != len(nodes):
        raise Invalid("the graph has a cycle; no topological order exists")
    return order

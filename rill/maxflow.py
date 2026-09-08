"""Max flow: the most a network can carry equals its narrowest cut, and only that cut matters.

The maximum throughput a capacitated network can push from a
source to a sink is not the sum of any one path's capacity but the
result of routing flow along many paths until no more can be
added, and the fact that makes it tractable is the max-flow
min-cut theorem: the most that can flow equals the capacity of the
cheapest cut, the minimum total capacity of edges whose removal
disconnects source from sink. That cut is the bottleneck, and the
practical consequence is sharp: adding capacity to an edge that is
not on the min cut does nothing for throughput, because the flow
was never limited there, while adding to a min-cut edge raises the
whole network's capacity until some other cut becomes the
bottleneck. Edmonds-Karp finds the max flow by repeatedly sending
flow along a shortest augmenting path in the residual network,
found by breadth-first search, subtracting the path's bottleneck
from forward capacities and adding it to reverse ones so later
paths can reroute earlier flow, until no augmenting path remains.
This module computes the max flow and, to make the theorem
concrete, lets a test raise a non-bottleneck edge and see the flow
unchanged, so the min cut being the only capacity that matters is a
measured result rather than a theorem cited.
"""

from __future__ import annotations

from collections import deque

from rill.errors import Invalid


def max_flow(
    capacity: dict[str, dict[str, int]], source: str, sink: str
) -> int:
    if source == sink:
        raise Invalid("source and sink must differ")
    residual: dict[str, dict[str, int]] = {}
    for node, edges in capacity.items():
        residual.setdefault(node, {})
        for neighbor, cap in edges.items():
            if cap < 0:
                raise Invalid("capacities cannot be negative")
            residual[node][neighbor] = residual[node].get(neighbor, 0) + cap
            residual.setdefault(neighbor, {}).setdefault(node, 0)
    total = 0
    while True:
        parent = _bfs(residual, source, sink)
        if parent is None:
            return total
        bottleneck = _bottleneck(residual, parent, source, sink)
        node = sink
        while node != source:
            prev = parent[node]
            residual[prev][node] -= bottleneck
            residual[node][prev] += bottleneck
            node = prev
        total += bottleneck


def _bfs(
    residual: dict[str, dict[str, int]], source: str, sink: str
) -> dict[str, str] | None:
    parent: dict[str, str] = {source: source}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for neighbor, cap in residual[node].items():
            if cap > 0 and neighbor not in parent:
                parent[neighbor] = node
                if neighbor == sink:
                    return parent
                queue.append(neighbor)
    return None


def _bottleneck(
    residual: dict[str, dict[str, int]], parent: dict[str, str], source: str, sink: str
) -> int:
    flow = float("inf")
    node = sink
    while node != source:
        prev = parent[node]
        flow = min(flow, residual[prev][node])
        node = prev
    return int(flow)

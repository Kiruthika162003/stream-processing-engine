"""Bellman-Ford: shortest paths with negative edges, and the cycle that has no answer.

Dijkstra's greedy finalization breaks on negative edges, and
Bellman-Ford is the slower method that survives them. It makes no
greedy commitment; instead it relaxes every edge repeatedly,
lowering each node's tentative distance whenever a shorter route
through some edge is found, and it repeats that full sweep as many
times as there are nodes minus one. That count is the guarantee: a
shortest path visits at most that many edges, so after that many
sweeps every reachable node's distance has settled, even routes
whose advantage only appears once a negative edge downstream is
counted. The price is O(V times E), a sweep over all edges once
per node, far more than Dijkstra's heap-driven pass, paid for the
ability to handle the negatives Dijkstra cannot. Negatives also
introduce a failure that has no answer rather than a wrong one: a
cycle whose edges sum to a negative can be looped forever to lower
a path without bound, so no shortest path exists. Bellman-Ford
detects it by running one more sweep after the last, and if any
edge still relaxes, a negative cycle is present. This module
computes the distances, and reports a negative cycle rather than
returning a meaningless finite number.
"""

from __future__ import annotations

from rill.errors import Halted, Invalid, Missing


def shortest_distance(
    nodes: list[str], edges: list[tuple[str, str, int]], source: str
) -> dict[str, int]:
    if source not in nodes:
        raise Invalid(f"unknown source {source}")
    distance: dict[str, float] = dict.fromkeys(nodes, float("inf"))
    distance[source] = 0
    for _ in range(len(nodes) - 1):
        for origin, dest, weight in edges:
            distance[dest] = min(distance[dest], distance[origin] + weight)
    for origin, dest, weight in edges:
        if distance[origin] + weight < distance[dest]:
            raise Halted("a negative cycle makes shortest paths unbounded")
    return {node: int(dist) for node, dist in distance.items() if dist != float("inf")}


def distance_to(
    nodes: list[str], edges: list[tuple[str, str, int]], source: str, target: str
) -> int:
    distances = shortest_distance(nodes, edges, source)
    if target not in distances:
        raise Missing(f"no path from {source} to {target}")
    return distances[target]

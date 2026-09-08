"""Dijkstra: the lowest-cost path by always finalizing the nearest unvisited node.

Routing to the lowest-latency path through a network of nodes and
weighted links is Dijkstra's problem, and its engine is a greedy
invariant: repeatedly take the unvisited node with the smallest
known distance, finalize it, and relax its edges, lowering
neighbors' tentative distances. Finalizing the nearest node is
safe because every other route to it would have to pass through
some other unvisited node that is already at least as far, so no
shorter path to it can still be discovered. A min-heap keyed by
tentative distance makes taking the nearest node cheap, giving E
log V overall. The invariant rests entirely on edge weights being
non-negative: a negative edge could make a longer-looking route
actually shorter after the fact, so a node finalized as nearest
might have a cheaper path through a node visited later, and the
greedy choice becomes wrong, which is why negative weights need a
different algorithm and are refused here rather than silently
mishandled. This module runs the search with a heap and returns
the distance and the path, so the shortest route is a computed
result and the non-negativity the method depends on is an explicit
precondition.
"""

from __future__ import annotations

import heapq

from rill.errors import Invalid, Missing


def shortest_path(
    graph: dict[str, list[tuple[str, int]]], source: str, target: str
) -> tuple[int, list[str]]:
    if source not in graph:
        raise Invalid(f"unknown source {source}")
    for edges in graph.values():
        if any(weight < 0 for _, weight in edges):
            raise Invalid("Dijkstra requires non-negative edge weights")
    distance = {source: 0}
    previous: dict[str, str] = {}
    heap: list[tuple[int, str]] = [(0, source)]
    visited: set[str] = set()
    while heap:
        dist, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node == target:
            break
        for neighbor, weight in graph.get(node, []):
            candidate = dist + weight
            if candidate < distance.get(neighbor, float("inf")):
                distance[neighbor] = candidate
                previous[neighbor] = node
                heapq.heappush(heap, (candidate, neighbor))
    if target not in distance:
        raise Missing(f"no path from {source} to {target}")
    path = [target]
    while path[-1] != source:
        path.append(previous[path[-1]])
    path.reverse()
    return distance[target], path

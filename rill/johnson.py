"""Johnson's algorithm: all-pairs shortest paths that survive negative edges.

Finding the shortest path between every pair of nodes has an easy
answer when edges are non-negative: run Dijkstra from each source,
which is fast on sparse graphs. But Dijkstra breaks on negative
edges, and the alternative that tolerates them, Floyd-Warshall, is
cubic in the node count regardless of how few edges there are, so it
wastes effort on sparse graphs. Johnson's algorithm gets the best of
both: it runs Dijkstra from every source, keeping the sparse-graph
speed, but first reweights the edges so they are all non-negative
while preserving which paths are shortest. The reweighting uses
potentials. Add a virtual source connected to every node by a
zero-weight edge and run Bellman-Ford once from it, which both
detects a negative cycle, in which case shortest paths are undefined
and the honest response is to refuse, and yields a potential for each
node, its shortest distance from the virtual source. The new weight
of an edge from u to v is its old weight plus the potential of u
minus the potential of v. This is non-negative exactly because the
potentials satisfy the triangle inequality Bellman-Ford enforces, and
it shifts every path from u to v by the same potential difference, so
the shortest path is unchanged and only its recorded length must be
corrected back afterward by subtracting the endpoints' potential gap.
The finding worth stating is that one Bellman-Ford pass buys the
right to use Dijkstra everywhere else, trading a cubic algorithm for
a near-linear-per-source one on sparse graphs. This module computes
all-pairs distances by Johnson, and a test checks them against
Floyd-Warshall including on graphs with negative edges, so the
reweighting is confirmed to preserve the true distances.
"""

from __future__ import annotations

import heapq

from rill.errors import Invalid

_INF = float("inf")


def _bellman_ford(nodes: list[int], edges: list[tuple[int, int, float]]) -> dict[int, float]:
    # virtual source with a zero edge to every node has potential 0 there
    dist = dict.fromkeys(nodes, 0.0)
    for _ in range(len(nodes)):
        changed = False
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:
            break
    for u, v, w in edges:
        if dist[u] + w < dist[v]:
            raise Invalid("graph has a negative cycle; shortest paths are undefined")
    return dist


def _dijkstra(source: int, adjacency: dict[int, list[tuple[int, float]]]) -> dict[int, float]:
    dist = {source: 0.0}
    heap = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, _INF):
            continue
        for v, w in adjacency[u]:
            nd = d + w
            if nd < dist.get(v, _INF):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def all_pairs(
    nodes: list[int], edges: list[tuple[int, int, float]]
) -> dict[int, dict[int, float]]:
    if nodes is None or edges is None:
        raise Invalid("nodes and edges must not be None")
    node_set = set(nodes)
    for u, v, _w in edges:
        if u not in node_set or v not in node_set:
            raise Invalid("every edge endpoint must be a listed node")
    potential = _bellman_ford(nodes, edges)
    adjacency: dict[int, list[tuple[int, float]]] = {n: [] for n in nodes}
    for u, v, w in edges:
        adjacency[u].append((v, w + potential[u] - potential[v]))
    result: dict[int, dict[int, float]] = {}
    for source in nodes:
        reduced = _dijkstra(source, adjacency)
        result[source] = {
            target: reduced[target] - potential[source] + potential[target]
            for target in reduced
        }
    return result

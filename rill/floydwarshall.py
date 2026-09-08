"""Floyd-Warshall: every shortest path at once, by letting each node be a possible waypoint.

When the shortest distance between every pair of nodes is needed
at once, a routing table across a whole cluster, running a
single-source search from each node works but is clumsy;
Floyd-Warshall computes the entire all-pairs matrix in one triply
nested pass. Its idea is disarmingly simple: consider each node in
turn as a permitted intermediate waypoint, and for every pair of
nodes ask whether routing through that waypoint is shorter than
the best route found so far without it. After every node has had
its turn as a waypoint, the best route between each pair is
allowed to pass through any of them, which is the shortest path.
The order of the loops is the whole correctness: the waypoint loop
must be outermost, because the distances being combined must
already account for every earlier waypoint, and swapping the loop
order, a tempting simplification, silently computes wrong
distances. Floyd-Warshall handles negative edges, and a negative
cycle reveals itself as a node whose distance to itself has gone
below zero, since it could loop to lower its own path. The cost is
cubic in the node count, which is the price of every pair at once
rather than one source at a time. This module computes the matrix
and detects a negative cycle, so the all-pairs distances are a
result checked against a per-source search.
"""

from __future__ import annotations

from rill.errors import Halted, Invalid

INF = float("inf")


def all_pairs(
    nodes: list[str], edges: list[tuple[str, str, int]]
) -> dict[str, dict[str, float]]:
    if not nodes:
        raise Invalid("no nodes")
    dist = {a: {b: (0.0 if a == b else INF) for b in nodes} for a in nodes}
    for origin, dest, weight in edges:
        if origin not in dist or dest not in dist:
            raise Invalid("an edge names a node not in the node set")
        dist[origin][dest] = min(dist[origin][dest], weight)
    for waypoint in nodes:
        for a in nodes:
            through = dist[a][waypoint]
            if through == INF:
                continue
            for b in nodes:
                candidate = through + dist[waypoint][b]
                dist[a][b] = min(dist[a][b], candidate)
    for node in nodes:
        if dist[node][node] < 0:
            raise Halted("a negative cycle makes shortest paths unbounded")
    return dist

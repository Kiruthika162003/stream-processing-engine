"""Hierholzer: build a trail using every edge exactly once, in linear time.

An Eulerian trail walks a graph crossing every edge exactly once; a
closed one, returning to its start, is an Eulerian circuit. The
existence conditions are a classical result, and for a directed graph
they are crisp: the graph must be connected on its edges, and either
every vertex has in-degree equal to out-degree, giving a circuit, or
exactly one vertex has one more outgoing than incoming, the start,
and exactly one has one more incoming than outgoing, the end. When
those hold Hierholzer's algorithm constructs the trail in time linear
in the edge count, which is optimal since the trail names every edge.
It works by following unused edges from the start until it returns
and can go no further, forming a partial trail that may not yet cover
every edge. Then it scans that trail for a vertex still having unused
edges, walks a new closed detour from there consuming those edges,
and splices the detour into the trail at that vertex. Repeating until
no vertex has an unused edge yields a single trail covering all
edges, and the splicing is what makes it linear: each edge is walked
once when its detour is formed and never revisited. The finding worth
stating is that the greedy follow-until-stuck walk never wastes an
edge because every stuck point on an Eulerian graph is the start
vertex, by the degree balance, so the leftover edges always form
detours that splice cleanly. This module builds a directed Eulerian
trail with Hierholzer and refuses graphs failing the degree
conditions, and a test checks the trail uses each edge exactly once
and is a valid walk, so the construction is confirmed.
"""

from __future__ import annotations

from collections import defaultdict

from rill.errors import Invalid


def eulerian_trail(edges: list[tuple[int, int]]) -> list[int]:
    if edges is None:
        raise Invalid("edges must not be None")
    if not edges:
        return []
    out_adj: dict[int, list[int]] = defaultdict(list)
    out_deg: dict[int, int] = defaultdict(int)
    in_deg: dict[int, int] = defaultdict(int)
    for u, v in edges:
        out_adj[u].append(v)
        out_deg[u] += 1
        in_deg[v] += 1
    nodes = set(out_deg) | set(in_deg)
    start = next(iter(nodes))
    starts = ends = 0
    for node in nodes:
        diff = out_deg[node] - in_deg[node]
        if diff == 1:
            starts += 1
            start = node
        elif diff == -1:
            ends += 1
        elif diff != 0:
            raise Invalid("no Eulerian trail: a vertex is off by more than one")
    if not ((starts == 0 and ends == 0) or (starts == 1 and ends == 1)):
        raise Invalid("no Eulerian trail: the start and end degrees do not balance")
    # Hierholzer with an explicit stack; pointers avoid re-scanning adjacency
    ptr: dict[int, int] = defaultdict(int)
    stack = [start]
    trail: list[int] = []
    while stack:
        node = stack[-1]
        if ptr[node] < len(out_adj[node]):
            nxt = out_adj[node][ptr[node]]
            ptr[node] += 1
            stack.append(nxt)
        else:
            trail.append(stack.pop())
    trail.reverse()
    if len(trail) != len(edges) + 1:
        raise Invalid("no Eulerian trail: the graph's edges are not connected")
    return trail

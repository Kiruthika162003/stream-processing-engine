"""Articulation points: the vertices whose removal breaks a graph apart.

An articulation point, or cut vertex, is a node whose deletion, with
its incident edges, raises the number of connected components: remove
it and some part of the graph that was reachable becomes stranded. In
a network these are the single points of failure, the routers or
brokers whose loss partitions the system, so finding them all is a
resilience question worth one linear pass rather than a removal
experiment per vertex. Tarjan's method finds them in one depth-first
search using two stamps per node: the discovery time, the order the
search first reached it, and the low-link, the earliest discovery
time reachable from its subtree by tree edges and at most one back
edge. A non-root node u is a cut vertex exactly when it has a child
v in the search tree whose subtree cannot reach above u, that is the
low-link of v is at or below u's own discovery time, meaning the only
way out of v's subtree passes through u. The root of the search is
the exception that catches people out: it is a cut vertex if and only
if it has two or more children in the search tree, because one child
means the whole graph hung below it as a single piece, and the
at-or-below test does not apply to a node with nothing above it. The
finding worth stating is that the low-link at-or-below rule plus the
separate two-children rule for the root together catch every cut
vertex in one pass, no per-vertex removal. This module returns the
articulation points, and a test checks them against the brute
definition, removing each vertex and counting components, so the
one-pass rule is confirmed to agree with the meaning.
"""

from __future__ import annotations

from rill.errors import Invalid


def articulation_points(graph: dict[int, list[int]]) -> set[int]:
    if graph is None:
        raise Invalid("graph must not be None")
    disc: dict[int, int] = {}
    low: dict[int, int] = {}
    timer = 0
    cuts: set[int] = set()

    def dfs(root: int) -> None:
        nonlocal timer
        # iterative DFS; frame carries the node, its parent, and a child index
        stack: list[list[int]] = [[root, -1, 0]]
        root_children = 0
        while stack:
            frame = stack[-1]
            node, parent, idx = frame
            if idx == 0:
                disc[node] = low[node] = timer
                timer += 1
            neighbors = graph.get(node, [])
            if idx < len(neighbors):
                frame[2] += 1
                nxt = neighbors[idx]
                if nxt == parent:
                    continue
                if nxt in disc:
                    low[node] = min(low[node], disc[nxt])
                else:
                    stack.append([nxt, node, 0])
            else:
                stack.pop()
                if stack:
                    par = stack[-1][0]
                    low[par] = min(low[par], low[node])
                    if stack[-1][1] != -1 and low[node] >= disc[par]:
                        cuts.add(par)
                    elif stack[-1][1] == -1:
                        root_children += 1
        if root_children >= 2:
            cuts.add(root)

    for start in graph:
        if start not in disc:
            dfs(start)
    return cuts

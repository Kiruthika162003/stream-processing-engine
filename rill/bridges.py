"""Bridges: the edges whose loss splits the network, the single points of failure to find.

In a network of nodes and undirected links, a bridge is an edge
whose removal disconnects the graph, splitting it into pieces that
can no longer reach each other. Bridges are the single points of
failure worth knowing before they fail: a link that is a bridge
has no alternate path around it, so losing it partitions the
cluster, while a link on a cycle has a detour and its loss is
survivable. Finding bridges by removing each edge and testing
connectivity is quadratic; Tarjan's method finds them all in one
depth-first traversal. As the DFS explores, it stamps each node
with a discovery time and computes a low-link, the earliest
discovery time reachable from that node's subtree using at most
one back-edge, and an edge from a node to a child is a bridge
exactly when the child's low-link is strictly greater than the
parent's discovery time, meaning the child's subtree has no
back-edge climbing above the parent, so nothing routes around the
edge. That single inequality captures the whole notion of an edge
being on no cycle. This module finds the bridges in one pass, so
the links whose failure would partition the network are a computed
list rather than a fault discovered in production.
"""

from __future__ import annotations

from rill.errors import Invalid


def find_bridges(
    nodes: list[str], edges: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for a, b in edges:
        if a not in adjacency or b not in adjacency:
            raise Invalid("an edge names a node not in the node set")
        adjacency[a].append(b)
        adjacency[b].append(a)

    disc: dict[str, int] = {}
    low: dict[str, int] = {}
    timer = [0]
    found: list[tuple[str, str]] = []

    def dfs(node: str, parent: str | None) -> None:
        disc[node] = low[node] = timer[0]
        timer[0] += 1
        skipped_parent = False
        for neighbor in adjacency[node]:
            if neighbor == parent and not skipped_parent:
                skipped_parent = True
                continue
            if neighbor not in disc:
                dfs(neighbor, node)
                low[node] = min(low[node], low[neighbor])
                if low[neighbor] > disc[node]:
                    found.append(tuple(sorted((node, neighbor))))
            else:
                low[node] = min(low[node], disc[neighbor])

    for node in nodes:
        if node not in disc:
            dfs(node, None)
    return sorted(set(found))

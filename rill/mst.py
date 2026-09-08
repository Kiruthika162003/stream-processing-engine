"""Minimum spanning tree: the greedy that is provably optimal, unlike knapsack's or coin's.

Connecting a set of nodes with the cheapest total edge weight, a
minimum spanning tree, is where greedy finally wins outright,
which is worth stating because so many other selection problems,
the knapsack, non-canonical coin change, punish the greedy that
looks obvious. Kruskal's algorithm sorts the edges by weight and
adds each one that connects two so-far-separate components,
skipping any edge whose endpoints are already joined because it
would form a cycle without connecting anything new. The union-find
structure tracks which nodes are already in the same component so
the cycle check is near constant. What makes this greedy optimal
where the others fail is the cut property: for any way of
splitting the nodes into two groups, the cheapest edge crossing
the split must be in some minimum spanning tree, and Kruskal only
ever adds such cheapest-crossing edges, so it never has to reverse
a choice. That is the structural difference from the knapsack,
where taking the locally best item can foreclose a better
combination; here the locally cheapest connecting edge is always
safe. This module runs Kruskal and returns the tree's total
weight, so the optimal connection cost is a computed result and
the case where greedy is right stands beside the cases where it
is not.
"""

from __future__ import annotations

from rill.errors import Invalid, Missing


def _find(parent: dict[str, str], node: str) -> str:
    root = node
    while parent[root] != root:
        root = parent[root]
    while parent[node] != root:
        parent[node], node = root, parent[node]
    return root


def mst_weight(nodes: list[str], edges: list[tuple[str, str, int]]) -> int:
    if not nodes:
        raise Invalid("no nodes")
    parent = {node: node for node in nodes}
    components = len(nodes)
    total = 0
    for weight, (origin, dest) in sorted((w, (a, b)) for a, b, w in edges):
        if origin not in parent or dest not in parent:
            raise Invalid("an edge names a node not in the node set")
        root_a, root_b = _find(parent, origin), _find(parent, dest)
        if root_a != root_b:
            parent[root_a] = root_b
            total += weight
            components -= 1
    if components != 1:
        raise Missing("the graph is disconnected; no spanning tree exists")
    return total

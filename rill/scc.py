"""Strongly connected components: the maximal cycles in a graph, and the DAG they collapse to.

A directed graph's strongly connected components are its maximal
sets of nodes where every node can reach every other, the true
cycles of the graph as opposed to the incidental back-edges a
plain cycle check reports. Finding them matters because collapsing
each component to a single node turns any directed graph into a
directed acyclic one, its condensation, which can then be
topologically ordered even though the original could not. In a
stream topology the strongly connected components are exactly the
feedback loops, the groups of operators that mutually depend and
must be scheduled or reasoned about together, and a graph with no
component larger than one node is acyclic. Kosaraju's algorithm
finds them in two linear passes: a depth-first traversal that
records nodes in order of completion, then a second traversal over
the edge-reversed graph taking nodes in reverse completion order,
where each tree grown is one strongly connected component. The
reversal is the insight, because a node and everything reachable
from it in both the original and the reversed graph is precisely
its component. This module computes the components, so the cycles
a graph actually contains, and the acyclic condensation they
collapse to, are a computed partition rather than a yes-or-no on
whether a cycle exists.
"""

from __future__ import annotations

from rill.errors import Invalid


def strongly_connected_components(
    nodes: list[str], edges: list[tuple[str, str]]
) -> list[set[str]]:
    forward: dict[str, list[str]] = {node: [] for node in nodes}
    backward: dict[str, list[str]] = {node: [] for node in nodes}
    for origin, dest in edges:
        if origin not in forward or dest not in forward:
            raise Invalid("an edge names a node not in the node set")
        forward[origin].append(dest)
        backward[dest].append(origin)

    order: list[str] = []
    seen: set[str] = set()

    def visit(start: str) -> None:
        stack = [(start, iter(forward[start]))]
        seen.add(start)
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if child not in seen:
                    seen.add(child)
                    stack.append((child, iter(forward[child])))
                    advanced = True
                    break
            if not advanced:
                order.append(node)
                stack.pop()

    for node in nodes:
        if node not in seen:
            visit(node)

    assigned: set[str] = set()
    components: list[set[str]] = []
    for root in reversed(order):
        if root in assigned:
            continue
        component: set[str] = set()
        stack = [root]
        assigned.add(root)
        while stack:
            node = stack.pop()
            component.add(node)
            for prev in backward[node]:
                if prev not in assigned:
                    assigned.add(prev)
                    stack.append(prev)
        components.append(component)
    return components

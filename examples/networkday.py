"""A network day: shortest paths, a spanning tree, a bottleneck, a cycle, and a weak link.

Run with: python -m examples.networkday
"""

from __future__ import annotations

from rill.bridges import find_bridges
from rill.dijkstra import shortest_path
from rill.maxflow import max_flow
from rill.mst import mst_weight
from rill.scc import strongly_connected_components


def morning_the_shortest_path():
    graph = {
        "s": [("a", 1), ("b", 4)],
        "a": [("b", 2), ("t", 5)],
        "b": [("t", 1)],
        "t": [],
    }
    distance, path = shortest_path(graph, "s", "t")
    print(f"route:    cost {distance} via {'-'.join(path)}")


def midday_the_spanning_tree():
    nodes = ["A", "B", "C", "D"]
    edges = [("A", "B", 1), ("B", "C", 2), ("A", "C", 2), ("C", "D", 3), ("B", "D", 5)]
    print(f"tree:     minimum spanning weight {mst_weight(nodes, edges)}")


def afternoon_the_bottleneck():
    graph = {"s": {"a": 10, "b": 10}, "a": {"b": 2, "t": 8}, "b": {"t": 10}}
    print(f"flow:     max flow s to t is {max_flow(graph, 's', 't')}")


def dusk_the_cycle():
    nodes = ["A", "B", "C", "D"]
    edges = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D")]
    biggest = max(strongly_connected_components(nodes, edges), key=len)
    print(f"cycle:    largest feedback loop {sorted(biggest)}")


def night_the_weak_link():
    nodes = ["A", "B", "C", "D"]
    edges = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D")]
    print(f"bridge:   single points of failure {find_bridges(nodes, edges)}")


def main() -> int:
    morning_the_shortest_path()
    midday_the_spanning_tree()
    afternoon_the_bottleneck()
    dusk_the_cycle()
    night_the_weak_link()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

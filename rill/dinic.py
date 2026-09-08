"""Dinic's algorithm: max flow by level graphs and blocking flows.

Maximum flow sends as much as possible from a source to a sink
through a capacitated network, and the textbook Edmonds-Karp finds it
by repeatedly pushing flow along one shortest augmenting path at a
time, breadth-first, which is correct but sends flow down one path
per search. Dinic's algorithm pushes many paths per search and is
faster on dense graphs. Each round has two phases. First a
breadth-first search from the source labels every node with its level,
its distance in edges along residual capacity, and keeps only edges
that step from one level to the next, forming the level graph, a
layered acyclic slice of the residual network. If the sink is
unreachable, no augmenting path remains and the flow is maximum.
Second, it finds a blocking flow in that level graph, saturating paths
by depth-first search until every source-to-sink route hits a full
edge, and crucially it advances a per-node pointer past edges already
exhausted so no dead edge is walked twice within the phase. Each
blocking-flow phase strictly increases the sink's level in the next
round, so there are at most a node-count of phases, and that bound is
what makes Dinic asymptotically better than pushing single paths. The
correctness rests on the same max-flow-min-cut foundation as every
augmenting method: when the residual graph disconnects source from
sink, the saturated edges across that cut prove the flow cannot be
larger. The finding worth stating is that the level graph plus the
dead-edge pointer turn many augmenting paths into one blocking-flow
sweep, cutting the number of searches. This module computes max flow
by Dinic, and a test checks its value against a brute augmenting-path
max flow on random networks, so the layered method is confirmed to
find the true maximum.
"""

from __future__ import annotations

from collections import deque

from rill.errors import Invalid


class Dinic:
    def __init__(self, n: int) -> None:
        if n <= 0:
            raise Invalid("node count must be positive")
        self._n = n
        self._to: list[int] = []
        self._cap: list[int] = []
        self._head: list[list[int]] = [[] for _ in range(n)]

    def add_edge(self, u: int, v: int, capacity: int) -> None:
        if not (0 <= u < self._n and 0 <= v < self._n):
            raise Invalid("edge endpoints must be valid nodes")
        if capacity < 0:
            raise Invalid("capacity must not be negative")
        self._head[u].append(len(self._to))
        self._to.append(v)
        self._cap.append(capacity)
        self._head[v].append(len(self._to))
        self._to.append(u)
        self._cap.append(0)

    def _levels(self, source: int, sink: int) -> list[int]:
        level = [-1] * self._n
        level[source] = 0
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for eid in self._head[u]:
                v = self._to[eid]
                if self._cap[eid] > 0 and level[v] == -1:
                    level[v] = level[u] + 1
                    queue.append(v)
        return level if level[sink] != -1 else []

    def _push(self, u: int, sink: int, flow: int, level: list[int], it: list[int]) -> int:
        if u == sink:
            return flow
        while it[u] < len(self._head[u]):
            eid = self._head[u][it[u]]
            v = self._to[eid]
            if self._cap[eid] > 0 and level[v] == level[u] + 1:
                pushed = self._push(v, sink, min(flow, self._cap[eid]), level, it)
                if pushed > 0:
                    self._cap[eid] -= pushed
                    self._cap[eid ^ 1] += pushed
                    return pushed
            it[u] += 1
        return 0

    def max_flow(self, source: int, sink: int) -> int:
        if not (0 <= source < self._n and 0 <= sink < self._n):
            raise Invalid("source and sink must be valid nodes")
        if source == sink:
            raise Invalid("source and sink must differ")
        total = 0
        while True:
            level = self._levels(source, sink)
            if not level:
                return total
            it = [0] * self._n
            while True:
                pushed = self._push(source, sink, float("inf"), level, it)
                if pushed == 0:
                    break
                total += pushed

"""The pipeline graph: operators wired into a DAG that must stay acyclic.

A streaming topology is a directed graph of operators, and
the one structural rule that cannot bend is acyclicity,
because a cycle in a stream is not a loop that terminates, it
is data feeding itself forever, a positive feedback that fills
memory and never drains. The builder refuses a cycle at wiring
time with the full loop named, since a cycle discovered at run
time is discovered by the machine running out of memory, the
most expensive possible place to learn about it. The graph
also answers the two questions an operator author needs: what
must run before this operator, its upstream closure, and what
this operator's failure takes down, its downstream closure,
because deploying an operator without knowing its blast radius
is deploying blind, and the topological order the scheduler
needs falls out of the same structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class PipelineGraph:
    upstreams: dict[str, set[str]] = field(default_factory=dict)

    def add_operator(self, name: str) -> None:
        if name in self.upstreams:
            raise Invalid(f"{name} already in the graph")
        self.upstreams[name] = set()

    def wire(self, source: str, sink: str) -> str:
        for node in (source, sink):
            if node not in self.upstreams:
                raise Invalid(f"{node} is not in the graph")
        path = self._path(source, sink)
        if path is not None:
            loop = " -> ".join([*path, source])
            raise Invalid(
                f"wiring {source} -> {sink} closes a cycle "
                f"({loop}); a stream cycle feeds itself forever "
                "and is discovered at run time by running out "
                "of memory"
            )
        self.upstreams[sink].add(source)
        return f"{source} -> {sink} wired"

    def _path(self, start: str, goal: str) -> list[str] | None:
        if start == goal:
            return [start]
        for upstream in self.upstreams.get(start, set()):
            found = self._path(upstream, goal)
            if found is not None:
                return [start, *found]
        return None

    def upstream_closure(self, name: str) -> set[str]:
        if name not in self.upstreams:
            raise Invalid(f"{name} is not in the graph")
        reached: set[str] = set()
        frontier = list(self.upstreams[name])
        while frontier:
            current = frontier.pop()
            if current not in reached:
                reached.add(current)
                frontier.extend(self.upstreams.get(current, set()))
        return reached

    def downstream_closure(self, name: str) -> set[str]:
        if name not in self.upstreams:
            raise Invalid(f"{name} is not in the graph")
        reached: set[str] = set()
        frontier = [
            sink
            for sink, ups in self.upstreams.items()
            if name in ups
        ]
        while frontier:
            current = frontier.pop()
            if current not in reached:
                reached.add(current)
                frontier.extend(
                    sink
                    for sink, ups in self.upstreams.items()
                    if current in ups
                )
        return reached

    def topological_order(self) -> list[str]:
        order: list[str] = []
        placed: set[str] = set()
        while len(placed) < len(self.upstreams):
            progressed = False
            for node in sorted(self.upstreams):
                if node in placed:
                    continue
                if self.upstreams[node] <= placed:
                    order.append(node)
                    placed.add(node)
                    progressed = True
            if not progressed:
                raise Invalid("the graph is not acyclic")
        return order

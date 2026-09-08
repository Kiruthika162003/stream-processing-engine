"""The topology: a graph of stages that refuses to become a loop.

A streaming job is a directed graph, sources at the top,
sinks at the bottom, and the graph's first duty is refusing
cycles at wiring time with the loop spelled out, because a
cycle in a streaming topology is not an error message at
runtime, it is an event that visits the same operator forever
while the metrics look busy. The second duty is naming the
dead parts before they run: a stage no source can reach will
never see an event, a stage that reaches no sink does work
nobody receives, and both are wiring mistakes that runtime
happily hides, the first as silence and the second as cost.
The parallelism plan multiplies each stage by its worker
count and prices the whole job in slots, since the scheduler
downstream of this graph thinks in slots and the graph should
speak its language.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Topology:
    stages: dict[str, int] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=dict)
    sources: set[str] = field(default_factory=set)
    sinks: set[str] = field(default_factory=set)

    def add_stage(
        self,
        name: str,
        parallelism: int = 1,
        source: bool = False,
        sink: bool = False,
    ) -> None:
        if name in self.stages:
            raise Invalid(f"{name} is already wired")
        if parallelism < 1:
            raise Invalid(f"{name} needs at least one worker")
        self.stages[name] = parallelism
        self.edges[name] = []
        if source:
            self.sources.add(name)
        if sink:
            self.sinks.add(name)

    def wire(self, upstream: str, downstream: str) -> None:
        for name in (upstream, downstream):
            if name not in self.stages:
                raise Invalid(f"{name} is not a stage")
        trail = self._path(downstream, upstream)
        if trail is not None:
            loop = " -> ".join([upstream, *trail])
            raise Invalid(
                f"wiring {upstream} -> {downstream} closes the "
                f"loop {loop}; an event would visit the same "
                "operator forever while the metrics look busy"
            )
        self.edges[upstream].append(downstream)

    def _path(
        self, start: str, goal: str
    ) -> list[str] | None:
        trail = {start: [start]}
        frontier = [start]
        while frontier:
            current = frontier.pop(0)
            if current == goal:
                return trail[current]
            for nxt in self.edges.get(current, []):
                if nxt not in trail:
                    trail[nxt] = trail[current] + [nxt]
                    frontier.append(nxt)
        return None

    def _reachable_from_sources(self) -> set[str]:
        seen: set[str] = set()
        frontier = list(self.sources)
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            seen.add(current)
            frontier.extend(self.edges.get(current, []))
        return seen

    def _reaching_sinks(self) -> set[str]:
        reaches: set[str] = set(self.sinks)
        changed = True
        while changed:
            changed = False
            for stage, downs in self.edges.items():
                if stage not in reaches and any(
                    down in reaches for down in downs
                ):
                    reaches.add(stage)
                    changed = True
        return reaches

    def wiring_review(self) -> str:
        if not self.sources or not self.sinks:
            raise Invalid(
                "a topology needs at least one source and one "
                "sink to mean anything"
            )
        fed = self._reachable_from_sources()
        heard = self._reaching_sinks()
        silent = sorted(set(self.stages) - fed)
        unheard = sorted(
            set(self.stages) - heard - set(self.sinks)
        )
        problems = []
        for stage in silent:
            problems.append(
                f"{stage}: no source reaches it; it will run "
                "as silence"
            )
        for stage in unheard:
            if stage in silent:
                continue
            problems.append(
                f"{stage}: reaches no sink; it will run as "
                "cost"
            )
        if not problems:
            return (
                f"{len(self.stages)} stage(s) wired, every one "
                "fed and heard"
            )
        return "\n".join(
            [f"{len(problems)} wiring mistake(s):"]
            + [f"  {problem}" for problem in problems]
        )

    def slot_bill(self) -> str:
        total = sum(self.stages.values())
        widest = max(
            self.stages, key=lambda name: self.stages[name]
        )
        return (
            f"{total} slot(s) across {len(self.stages)} "
            f"stage(s); {widest} is widest at "
            f"{self.stages[widest]}, the scheduler thinks in "
            "slots and this graph speaks its language"
        )

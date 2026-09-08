"""Branching a stream: every event takes exactly one door, and doors sum.

Routing splits one stream into many by predicate, and the two
invariants that make a split trustworthy are exhaustiveness
and exclusivity: every event matches exactly one branch, so
the branch counts sum to the input count, and the audit is
that addition, run continuously. The default branch is the
honesty valve: rather than silently dropping the event no
predicate wanted, it catches the remainder, and a default
that grows is the report's loudest line, because the
remainder is where the new event type lands the day another
team starts emitting it, and a fat default is the first
anyone hears of it. Overlapping predicates are caught at
wiring time by probe, since an event matching two branches
gets double-counted downstream, and double counting is the
bug that survives until finance reconciles.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.errors import Invalid
from rill.events import Event

Predicate = Callable[[Event], bool]


@dataclass
class StreamBranch:
    branches: list[tuple[str, Predicate]] = field(
        default_factory=list
    )
    counts: dict[str, int] = field(default_factory=dict)
    total_in: int = 0

    def add_branch(
        self, name: str, predicate: Predicate
    ) -> None:
        if any(held == name for held, _ in self.branches):
            raise Invalid(f"{name} already exists")
        self.branches.append((name, predicate))
        self.counts.setdefault(name, 0)

    def probe_overlap(self, probes: list[Event]) -> str:
        for event in probes:
            matched = [
                name
                for name, predicate in self.branches
                if predicate(event)
            ]
            if len(matched) > 1:
                raise Invalid(
                    f"probe {event.key} matches "
                    f"{' and '.join(matched)}: an event in two "
                    "branches is double-counted downstream, "
                    "the bug that survives until finance "
                    "reconciles"
                )
        return f"{len(probes)} probe(s), no overlap"

    def route(self, event: Event) -> str:
        self.total_in += 1
        for name, predicate in self.branches:
            if predicate(event):
                self.counts[name] = self.counts.get(name, 0) + 1
                return name
        self.counts["default"] = (
            self.counts.get("default", 0) + 1
        )
        return "default"

    def conservation_audit(self) -> str:
        routed = sum(self.counts.values())
        if routed != self.total_in:
            return (
                f"LEAK: {self.total_in} in, {routed} routed; "
                "events are vanishing between the doors"
            )
        default_count = self.counts.get("default", 0)
        lines = [
            f"{self.total_in} in, {routed} out; the doors sum"
        ]
        if default_count:
            share = 100 * default_count // self.total_in
            lines.append(
                f"the default holds {default_count} "
                f"({share}%): the remainder is where the new "
                "event type lands, and a fat default is the "
                "first anyone hears of it"
            )
        return "\n".join(lines)

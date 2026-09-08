"""The global window: no time boundary, so the trigger is the only thing firing it.

Most windows close on time; the global window never does, it
holds all of a key's events forever, which sounds useless
until you need aggregations that are not time-shaped, a
running total that emits every hundred events, a machine-
learning feature updated on a count trigger, a session that
ends on an explicit terminator event rather than a timeout.
The global window's whole design is that without a trigger it
accumulates without bound and emits nothing, so a global
window with no trigger declared is not a window, it is a
memory leak with a schema, and the module refuses to create
one. The count and delta triggers fire on data-shaped
conditions instead of clock-shaped ones, and the purge policy
is the other half nobody plans: firing a global window emits a
result but does not by default clear the state, so a global
window that fires and keeps accumulating grows forever, and
the choice to purge-on-fire or keep must be explicit because
the two produce different answers and different memory curves.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

TRIGGERS = ("count", "terminator")


@dataclass
class GlobalWindow:
    trigger: str
    count_threshold: int = 0
    purge_on_fire: bool = True
    total: int = 0
    seen: int = 0
    fired: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.trigger not in TRIGGERS:
            raise Invalid(
                f"a global window needs a trigger from "
                f"{TRIGGERS}; without one it is a memory leak "
                "with a schema"
            )
        if self.trigger == "count" and self.count_threshold < 1:
            raise Invalid("a count trigger needs a threshold")

    def add(
        self, value: int, is_terminator: bool = False
    ) -> str | None:
        self.total += value
        self.seen += 1
        should_fire = (
            self.trigger == "count"
            and self.seen >= self.count_threshold
        ) or (self.trigger == "terminator" and is_terminator)
        if not should_fire:
            return None
        result = self.total
        self.fired.append(result)
        if self.purge_on_fire:
            self.total = 0
            self.seen = 0
            return (
                f"fired {result} and purged; state cleared, "
                "the next window starts empty"
            )
        return (
            f"fired {result} and kept; state grows, a "
            "different answer and a different memory curve"
        )

    def memory_note(self) -> str:
        if self.purge_on_fire:
            return "purge-on-fire: bounded memory between firings"
        return (
            f"keep-on-fire: {self.seen} event(s) held and "
            "growing; chosen deliberately, not defaulted, "
            "because it grows forever"
        )

"""Load shedding: when something must be dropped, rank what the drop costs.

Backpressure holds the line until the line reaches the
source, and some sources cannot pause, the sensor keeps
sensing, the exchange keeps trading, so past that point the
pipeline sheds load, and shedding without a policy is a
policy of dropping whatever arrived at the wrong moment. The
shedder ranks event classes by declared value, drops from the
bottom tier first, and meters every drop by class, because
"we shed some load" is an incident footnote while "we dropped
40,000 telemetry pings and zero payments" is a defensible
decision made in advance. The tier list is refused if any
class is unranked, since the unranked class is the one that
gets dropped by accident, and accident is the only
indefensible policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class LoadShedder:
    tiers: dict[str, int]
    capacity_per_tick: int
    admitted: dict[str, int] = field(default_factory=dict)
    dropped: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.capacity_per_tick < 1:
            raise Invalid("capacity must be positive")
        if not self.tiers:
            raise Invalid("shedding needs a tier list")

    def tick(self, arrivals: dict[str, int]) -> str:
        for event_class in arrivals:
            if event_class not in self.tiers:
                raise Invalid(
                    f"{event_class} is unranked, and the "
                    "unranked class is the one that gets "
                    "dropped by accident"
                )
        budget = self.capacity_per_tick
        by_value = sorted(
            arrivals,
            key=lambda event_class: -self.tiers[event_class],
        )
        notes = []
        for event_class in by_value:
            count = arrivals[event_class]
            taken = min(count, budget)
            budget -= taken
            self.admitted[event_class] = (
                self.admitted.get(event_class, 0) + taken
            )
            shed = count - taken
            if shed:
                self.dropped[event_class] = (
                    self.dropped.get(event_class, 0) + shed
                )
                notes.append(
                    f"shed {shed} {event_class} (tier "
                    f"{self.tiers[event_class]})"
                )
        if not notes:
            return "everything admitted; no shedding this tick"
        return "; ".join(notes)

    def incident_footnote(self) -> str:
        if not self.dropped and not self.admitted:
            raise Invalid("nothing has passed through")
        parts = []
        for event_class in sorted(
            self.tiers, key=lambda name: -self.tiers[name]
        ):
            dropped = self.dropped.get(event_class, 0)
            parts.append(f"{dropped} {event_class}")
        return (
            "dropped " + ", ".join(parts) + "; a defensible "
            "decision made in advance, not an accident made "
            "under load"
        )

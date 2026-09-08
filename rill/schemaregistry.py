"""Schema evolution: the producer and consumer never deploy at the same instant.

Event schemas change, and the moment they do, some producers
run the new schema while some consumers still run the old, or
the reverse, so a schema change is safe only if it survives
that skew in both directions. Backward compatible means new
consumers read old events, forward compatible means old
consumers read new events, and full compatibility means both,
which is the only safe kind when you cannot control deploy
order. The registry classifies each proposed change: adding
an optional field is full, removing a field breaks forward,
adding a required field breaks backward, and renaming breaks
both because a rename is a remove plus an add wearing one
commit. The gate refuses a breaking change unless the
producer declares a migration window in which both schemas
are served, because a schema change deployed as an atomic
swap assumes an atomic fleet, and fleets are never atomic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass(frozen=True)
class Schema:
    version: int
    required: frozenset[str]
    optional: frozenset[str]

    def fields(self) -> frozenset[str]:
        return self.required | self.optional


def classify(old: Schema, new: Schema) -> str:
    added = new.fields() - old.fields()
    removed = old.fields() - new.fields()
    new_required = new.required - old.required
    added_required = new_required & added
    breaks_backward = bool(added_required)
    breaks_forward = bool(removed)
    if not breaks_backward and not breaks_forward:
        return "full"
    if breaks_backward and breaks_forward:
        return "none"
    if breaks_backward:
        return "forward-only"
    return "backward-only"


@dataclass
class SchemaRegistry:
    current: Schema
    migration_windows: dict[int, int] = field(
        default_factory=dict
    )

    def propose(
        self, new: Schema, migration_window: int = 0
    ) -> str:
        compatibility = classify(self.current, new)
        if compatibility == "full":
            self.current = new
            return (
                f"v{new.version} accepted: full compatibility, "
                "safe under any deploy order"
            )
        if migration_window < 1:
            raise Invalid(
                f"v{new.version} is {compatibility} compatible "
                "and needs a migration window serving both "
                "schemas; an atomic swap assumes an atomic "
                "fleet, and fleets are never atomic"
            )
        self.migration_windows[new.version] = migration_window
        self.current = new
        return (
            f"v{new.version} accepted with a "
            f"{migration_window}-window migration: "
            f"{compatibility} compatibility served both ways "
            "until the fleet converges"
        )

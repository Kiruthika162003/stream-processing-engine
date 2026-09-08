"""Live invariants: the assertion that runs in production, politely.

Tests assert on fixtures; invariant monitors assert on the
real stream, balance never negative, quantity never exceeds
inventory, refund never exceeds purchase, and the design
question is what to do when the impossible arrives, because
crashing the pipeline hands one bad event a denial of
service, and logging it hands it to nobody. The monitor's
answer is quarantine with context: the violating event, the
invariant's name, and the state that made it impossible,
captured together, while the stream continues past it, and
the escalation rule watches the rate, one violation is a bug
report, a burst is a corrupted upstream, and the monitor
says which. The invariant registry is versioned because
invariants are code: the balance rule that forgot about
refunds was not a violation storm, it was a wrong invariant,
and the monitor's history must be able to say so.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.errors import Invalid

Check = Callable[[int, int], bool]
BURST_THRESHOLD = 3


@dataclass
class InvariantMonitor:
    name: str
    version: int
    check: Check
    quarantined: list[str] = field(default_factory=list)
    passed: int = 0
    window_violations: int = 0

    def __post_init__(self) -> None:
        if self.version < 1:
            raise Invalid("invariants are code; code has versions")

    def observe(
        self, event_id: str, value: int, state: int
    ) -> str:
        if self.check(value, state):
            self.passed += 1
            return f"{event_id} consistent"
        entry = (
            f"{event_id}: {self.name} v{self.version} "
            f"violated with value {value} against state "
            f"{state}"
        )
        self.quarantined.append(entry)
        self.window_violations += 1
        return (
            f"QUARANTINED {entry}; the stream continues past "
            "it, because a crash hands one bad event a denial "
            "of service"
        )

    def escalation(self) -> str:
        if self.window_violations == 0:
            return f"{self.name}: quiet window"
        if self.window_violations < BURST_THRESHOLD:
            return (
                f"{self.name}: {self.window_violations} "
                "violation(s), a bug report"
            )
        return (
            f"{self.name}: {self.window_violations} "
            "violation(s) in one window, a corrupted upstream "
            "or a wrong invariant, and the version history "
            "must be able to say which"
        )

    def close_window(self) -> None:
        self.window_violations = 0

    def revise(self, new_check: Check) -> str:
        self.check = new_check
        self.version += 1
        return (
            f"{self.name} revised to v{self.version}; the "
            "balance rule that forgot about refunds was not a "
            "violation storm, it was a wrong invariant"
        )

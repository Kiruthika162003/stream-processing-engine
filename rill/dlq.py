"""The dead letter queue: the event that cannot be processed, kept for a verdict.

An event that fails processing has three possible futures and
a pipeline must choose deliberately: retry, because the
failure was transient; drop, because the event is genuinely
garbage; or quarantine in a dead letter queue, because the
failure needs a human. The wrong default is silent drop,
which turns a schema bug into missing data nobody notices, and
the second wrong default is infinite retry, which turns one
poison event into a stuck partition. The router applies a
retry budget then routes to the DLQ, and the DLQ is not a
graveyard but a workbench: each entry carries the failure
reason and the retry count so a human triaging it knows
whether to fix and replay, fix and drop, or escalate. The
DLQ's own size is a monitored signal, because a DLQ that only
grows is a bug nobody is fixing, and the age of its oldest
entry is the SLA nobody set but everybody has.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class DeadLetterRouter:
    max_retries: int
    attempts: dict[str, int] = field(default_factory=dict)
    dead_letters: dict[str, tuple[str, int]] = field(
        default_factory=dict
    )
    replayed: int = 0

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise Invalid("retry budget cannot be negative")

    def fail(self, event_id: str, reason: str) -> str:
        if not reason.strip():
            raise Invalid(
                "a failure without a reason cannot be triaged"
            )
        count = self.attempts.get(event_id, 0) + 1
        self.attempts[event_id] = count
        if count <= self.max_retries:
            return (
                f"{event_id} retry {count}/{self.max_retries}; "
                "transient until proven poison"
            )
        self.dead_letters[event_id] = (reason, count)
        return (
            f"{event_id} to the DLQ after {count} attempt(s): "
            f"{reason}; a workbench entry, not a silent drop"
        )

    def replay(self, event_id: str) -> str:
        if event_id not in self.dead_letters:
            raise Invalid(f"{event_id} is not in the DLQ")
        del self.dead_letters[event_id]
        self.attempts[event_id] = 0
        self.replayed += 1
        return f"{event_id} replayed after a human fixed the cause"

    def health(self, oldest_age: int, sla: int) -> str:
        size = len(self.dead_letters)
        if size == 0:
            return "DLQ empty; every event found a home"
        breach = (
            f", oldest entry {oldest_age} past the {sla} SLA "
            "nobody set but everybody has"
            if oldest_age > sla
            else ""
        )
        return (
            f"{size} dead letter(s), {self.replayed} replayed "
            f"over the DLQ's life{breach}; a DLQ that only "
            "grows is a bug nobody is fixing"
        )

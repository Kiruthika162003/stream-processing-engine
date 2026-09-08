"""The poison event: one bad record must not eat the whole stream.

Every long-lived stream eventually delivers the event that
crashes its operator, and the naive loop then retries it
forever: crash, restart, same offset, same event, same crash,
a pipeline bricked by one record while millions queue behind
it. The poison policy is a budget: an event that fails gets
retried a fixed number of times, because transient failures
deserve second chances, and past the budget it is quarantined
to the dead letter queue with its offset, its error, and its
attempt count, so the stream moves on and the record waits
for a human instead of holding a partition hostage. The
quarantine has its own alarm: poison arriving faster than a
threshold stops being a data problem and becomes a deploy
problem, because one bad record is a record and a hundred a
minute is a release.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

DEPLOY_SUSPICION = 3


@dataclass
class PoisonPolicy:
    retry_budget: int
    attempts: dict[str, int] = field(default_factory=dict)
    quarantined: list[str] = field(default_factory=list)
    recent_quarantines: int = 0

    def __post_init__(self) -> None:
        if self.retry_budget < 1:
            raise Invalid(
                "a budget of zero quarantines transient "
                "failures; even honest machinery hiccups"
            )

    def record_failure(
        self, offset: str, error: str
    ) -> str:
        count = self.attempts.get(offset, 0) + 1
        self.attempts[offset] = count
        if count <= self.retry_budget:
            return (
                f"{offset} failed (attempt {count} of "
                f"{self.retry_budget}); transient failures "
                "deserve second chances"
            )
        del self.attempts[offset]
        entry = (
            f"{offset}: {error} after {count} attempt(s)"
        )
        self.quarantined.append(entry)
        self.recent_quarantines += 1
        return (
            f"{offset} QUARANTINED after {count} attempt(s): "
            "the stream moves on, the record waits for a "
            "human, and the partition is no longer hostage"
        )

    def record_success(self, offset: str) -> str:
        healed = self.attempts.pop(offset, 0)
        if healed:
            return (
                f"{offset} succeeded on attempt {healed + 1}; "
                "the second chance was the right call"
            )
        return f"{offset} clean"

    def deploy_check(self) -> str:
        if self.recent_quarantines >= DEPLOY_SUSPICION:
            return (
                f"{self.recent_quarantines} quarantine(s) this "
                "window: one bad record is a record, this rate "
                "is a release; page the deploy owner, not the "
                "data owner"
            )
        return (
            f"{self.recent_quarantines} quarantine(s) this "
            "window; still a data problem"
        )

    def close_window(self) -> None:
        self.recent_quarantines = 0

    def dlq_page(self) -> str:
        if not self.quarantined:
            return "the dead letter queue is empty; enjoy it"
        lines = [
            f"{len(self.quarantined)} record(s) waiting for a "
            "human:"
        ]
        lines.extend(f"  {entry}" for entry in self.quarantined)
        return "\n".join(lines)

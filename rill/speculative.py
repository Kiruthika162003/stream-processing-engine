"""Speculative execution: a backup for the straggler, safe only if commits fence.

A task running far slower than its peers drags the whole stage's
completion behind it, and speculative execution answers by
launching a second copy of the straggler and taking whichever
finishes first. The idea is sound and the danger is exact: now
two copies of the same task are running, and if both are allowed
to commit their output the stage produces every one of the
straggler's results twice, which is worse than the slowness it
was fixing. Speculation is only safe when the commit is fenced so
that the first copy to finish wins and the second copy's commit
is refused as a no-op, its work thrown away rather than written.
This module decides when a task has lagged its siblings enough to
warrant a backup, tracks the attempts of a task, and gates their
commits so exactly one attempt's output lands no matter how many
copies raced. The slowness the backup removes is real, but the
duplicate it would introduce without the fence is the reason
naive speculation corrupts more than it accelerates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Speculator:
    slack: int
    _committed: dict[str, int] = field(default_factory=dict)
    _attempts: dict[str, set[int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.slack <= 0:
            raise Invalid("slack must be positive")

    def should_speculate(self, _task: str, elapsed: int, typical: int) -> bool:
        return elapsed > typical + self.slack

    def start(self, task: str, attempt: int) -> None:
        self._attempts.setdefault(task, set()).add(attempt)

    def commit(self, task: str, attempt: int) -> bool:
        if attempt not in self._attempts.get(task, set()):
            raise Invalid(f"attempt {attempt} of {task} never started")
        if task in self._committed:
            return False
        self._committed[task] = attempt
        return True

    def winner(self, task: str) -> int:
        if task not in self._committed:
            raise Invalid(f"{task} has not committed")
        return self._committed[task]

    def running_copies(self, task: str) -> int:
        return len(self._attempts.get(task, set()))

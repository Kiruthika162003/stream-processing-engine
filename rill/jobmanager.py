"""The job manager election: one brain, chosen by lease, fenced by term.

A stream job has one coordinator assigning partitions and
triggering checkpoints, and two coordinators believing they
lead is the split brain that assigns the same partition
twice. Leadership is a lease with a term number that only
increases: a candidate wins by acquiring the lease, every
command it issues carries its term, and the workers refuse
any command bearing a term older than the newest they have
obeyed, so the old leader waking from a pause cannot assign
anything because its term is stale. The term is the whole
safety argument, the lease only bounds how long a dead
leader's absence goes unnoticed, and the drill proves the
property that matters: an old coordinator's assignment,
issued after its replacement took the lease, is refused by
the worker with the term gap named, converting split brain
from a double-assignment into a log line.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid


@dataclass
class JobManagerElection:
    lease_holder: str | None = None
    term: int = 0
    lease_expires: int = 0
    worker_obeyed_term: int = 0
    fenced_commands: list[str] = field(default_factory=list)

    def acquire(self, candidate: str, now: int) -> str:
        if self.lease_holder is not None and now < self.lease_expires:
            raise Invalid(
                f"{self.lease_holder} holds the lease until "
                f"{self.lease_expires}; {candidate} waits"
            )
        self.lease_holder = candidate
        self.term += 1
        self.lease_expires = now + 30
        return f"{candidate} leads with term {self.term}"

    def assign(
        self, coordinator: str, term: int, partition: str
    ) -> str:
        if term < self.worker_obeyed_term:
            refusal = (
                f"{coordinator} assigns {partition} with term "
                f"{term} against obeyed {self.worker_obeyed_term}: "
                "a stale term is a woken zombie, and the "
                "assignment is a log line, not a double-assign"
            )
            self.fenced_commands.append(refusal)
            raise Halted(refusal)
        self.worker_obeyed_term = term
        return f"{partition} assigned under term {term}"

    def renew(self, holder: str, now: int) -> str:
        if holder != self.lease_holder:
            raise Invalid(
                f"{holder} cannot renew a lease it does not hold"
            )
        if now >= self.lease_expires:
            raise Invalid(
                f"{holder} renewed late; leadership lost by "
                "clock at {self.lease_expires}"
            )
        self.lease_expires = now + 30
        return f"{holder} renewed through {self.lease_expires}"

    def incident_summary(self) -> str:
        if not self.fenced_commands:
            return "no fenced commands; either no split brain or nobody assigned"
        return (
            f"{len(self.fenced_commands)} split-brain "
            "assignment(s) refused by term; the safety was "
            "the term, not the lease"
        )

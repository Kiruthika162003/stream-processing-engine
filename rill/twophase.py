"""Two-phase commit: the window after every yes where the coordinator can strand you.

Two-phase commit lands a change across several participants
atomically: the coordinator asks each to prepare, each votes yes
only if it can guarantee it will commit if told to, and the
coordinator commits if every vote is yes and aborts if any vote
is no. The protocol is correct and it has a hole nobody designs
out, only mitigates: a participant that voted yes has promised to
commit on command and so holds its locks, uncertain, until the
verdict arrives. If the coordinator crashes in the gap between
collecting the last yes and broadcasting the decision, those
yes-voters are stuck. They cannot commit on their own, another
participant might have voted no, and they cannot abort on their
own, the coordinator might already have decided commit, so they
block, holding locks, until the coordinator recovers and tells
them what it chose. This module runs the coordinator, tallies the
votes, records the one durable decision, and names the
participants blocked in that window, so the property 2PC is
infamous for is a measurable state and not a footnote.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid

COMMIT = "commit"
ABORT = "abort"


@dataclass
class TwoPhaseCoordinator:
    participants: tuple[str, ...]
    _votes: dict[str, bool] = field(default_factory=dict)
    _decision: str | None = None

    def __post_init__(self) -> None:
        if not self.participants:
            raise Invalid("a transaction needs at least one participant")

    def vote(self, participant: str, yes: bool) -> None:
        if participant not in self.participants:
            raise Invalid(f"{participant} is not in this transaction")
        if self._decision is not None:
            raise Halted("the decision is already made; votes are closed")
        self._votes[participant] = yes

    def all_voted(self) -> bool:
        return set(self._votes) == set(self.participants)

    def decide(self) -> str:
        if self._decision is not None:
            return self._decision
        if not self.all_voted():
            raise Invalid("cannot decide before every participant has voted")
        self._decision = COMMIT if all(self._votes.values()) else ABORT
        return self._decision

    def decided(self) -> bool:
        return self._decision is not None

    def outcome(self, participant: str) -> str:
        if participant not in self.participants:
            raise Invalid(f"{participant} is not in this transaction")
        if self._decision is None:
            raise Halted(
                f"{participant} voted and is blocked; the coordinator has "
                "not broadcast a decision"
            )
        return self._decision

    def blocked(self) -> list[str]:
        if self._decision is not None:
            return []
        return sorted(p for p, yes in self._votes.items() if yes)

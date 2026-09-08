"""Raft commit rule: a majority is not enough to commit an entry from an older term.

Raft commits a log entry once it is stored on a majority of
servers, but with one restriction that looks like a technicality
and is the whole safety of the protocol: a leader may only commit
an entry from its own current term by counting replicas. An entry
left over from a previous term, even replicated to a majority,
must not be declared committed on that basis, because a later
leader from a yet-higher term could still overwrite it, the
figure-eight scenario where an entry looks committed and then
vanishes. The rule threads it: the leader advances its commit
index to the highest entry that is both majority-replicated and
stamped with the current term, and committing that entry commits
every entry before it, including the stranded prior-term ones,
which are now safe because they sit beneath a current-term entry
that a majority has agreed on. So the old entry becomes committed
not when its own majority forms but when a new entry from this
term does. This module tracks the log terms and the per-follower
match indexes and computes the commit index under the real rule,
so the refusal to commit a prior-term entry on majority alone is
a test rather than a paragraph in the paper everyone skims.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class RaftLeader:
    servers: int
    current_term: int
    _log: list[int] = field(default_factory=list)
    _match: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.servers < 1:
            raise Invalid("need at least one server")
        if self.current_term < 1:
            raise Invalid("term starts at one")

    def append(self, term: int) -> int:
        if term > self.current_term:
            raise Invalid("cannot append an entry from a future term")
        self._log.append(term)
        return len(self._log)

    def replicated(self, follower: str, index: int) -> None:
        if not 0 <= index <= len(self._log):
            raise Invalid(f"index {index} is beyond the log")
        self._match[follower] = max(self._match.get(follower, 0), index)

    def _majority(self) -> int:
        return self.servers // 2 + 1

    def commit_index(self) -> int:
        majority = self._majority()
        best = 0
        for index in range(1, len(self._log) + 1):
            replicas = 1 + sum(1 for m in self._match.values() if m >= index)
            if replicas >= majority and self._log[index - 1] == self.current_term:
                best = index
        return best

"""Session guarantees: keeping a client's own view from running backward across replicas.

An eventually-consistent store lets a client read from any
replica, and the replicas are at different points in the log, so
a client that bounces between them can watch its own timeline
lurch backward: it sees a comment it just posted, its next read
lands on a lagging replica, and the comment is gone. The absolute
consistency of the whole system is not the fix here; the fix is
per-session, tracking what this one client has already observed
and refusing to show it anything older. Monotonic reads keep a
high-water version of what the client has seen and reject a read
from a replica behind it, so the client is routed to a
sufficiently caught-up replica rather than shown the past. Read-
your-writes extends the same high-water mark to include the
client's own writes, so after writing version V a read from a
replica that has not yet applied V is refused, guaranteeing the
client always sees at least its own effects. Neither guarantee
requires the replicas to agree with each other, only that no
single client is served a version below the highest it has
already established, which is the consistency a user actually
notices. This module tracks the session's high-water version and
admits or refuses a read against it.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid, Missing


@dataclass
class Session:
    _seen: int = 0

    def wrote(self, version: int) -> None:
        if version < 0:
            raise Invalid("version cannot be negative")
        self._seen = max(self._seen, version)

    def read(self, replica_version: int) -> int:
        if replica_version < 0:
            raise Invalid("version cannot be negative")
        if replica_version < self._seen:
            raise Missing(
                f"replica at {replica_version} is behind the session's "
                f"seen version {self._seen}; route to a fresher replica"
            )
        self._seen = replica_version
        return replica_version

    def seen(self) -> int:
        return self._seen

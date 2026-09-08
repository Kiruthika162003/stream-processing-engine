"""Bounded staleness: a read may be behind, but only by so much, or it is refused.

Strong consistency reads only the latest write and pays in
latency and availability; eventual consistency reads whatever a
replica has and can return arbitrarily old data. Bounded staleness
is the middle contract: a read may lag the latest write, but only
by a bounded amount, a number of versions or an interval of time,
and a replica further behind than the bound is not served. It is
the guarantee a dashboard or a cache actually wants, at most a few
seconds or a few versions stale, never unboundedly so. The
mechanism tracks the leader's current version and, on a read from
a replica, compares the replica's version to the leader's: within
the bound it serves, past the bound it refuses and the caller must
wait or route to a fresher replica. The trade the bound sets is
freshness against availability. A tight bound guarantees very
fresh reads but refuses more often, since more replicas fall
outside it during replication lag, and a loose bound serves almost
always but permits staler data. There is no bound that is both
maximally fresh and maximally available, which is the choice the
number encodes. This module tracks the leader version and admits
or refuses a read against the staleness bound, so the
freshness-for-availability trade is a decided number rather than
an accident of whichever replica answered.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid, Missing


@dataclass
class BoundedStaleness:
    max_lag: int
    _leader_version: int = 0

    def __post_init__(self) -> None:
        if self.max_lag < 0:
            raise Invalid("max lag cannot be negative")

    def leader_write(self) -> int:
        self._leader_version += 1
        return self._leader_version

    def leader_version(self) -> int:
        return self._leader_version

    def read(self, replica_version: int) -> int:
        if replica_version < 0 or replica_version > self._leader_version:
            raise Invalid("replica version out of range")
        if self._leader_version - replica_version > self.max_lag:
            raise Missing(
                f"replica is {self._leader_version - replica_version} versions "
                f"behind, past the staleness bound of {self.max_lag}"
            )
        return replica_version

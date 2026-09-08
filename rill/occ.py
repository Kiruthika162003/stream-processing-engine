"""Optimistic concurrency: bet on no conflict, validate at commit, and lose under contention.

Pessimistic locking takes a lock before touching data and pays
its cost whether or not anyone else was interested. Optimistic
concurrency control makes the opposite bet: read the data and its
version freely, do the work with no lock held, and only at commit
time check that the version has not changed since the read. If it
has not, the write applies and the version advances; if it has,
someone else committed in the meantime, the read the work was
based on is stale, and the commit is refused so the transaction
retries from a fresh read. The bet pays when conflicts are rare,
because the common case holds no lock and validates instantly, but
it turns against you under contention: when many transactions
target the same data, each other's commits keep invalidating the
rest, so a crowd of transactions can spend far more work retrying
than a lock would have cost, and in the worst case livelock,
retrying forever while making no progress. So OCC is the right
tool for a read-mostly, low-conflict workload and the wrong one
for a hot contended key, the mirror image of when locking wins.
This module keeps a versioned value, reads it, and validates a
commit against the version, so the conflict abort is a returned
verdict rather than a corrupted write.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class OccStore:
    _value: str = ""
    _version: int = 0

    def read(self) -> tuple[str, int]:
        return self._value, self._version

    def commit(self, expected_version: int, new_value: str) -> bool:
        if expected_version < 0:
            raise Invalid("version cannot be negative")
        if expected_version != self._version:
            return False
        self._value = new_value
        self._version += 1
        return True

    def version(self) -> int:
        return self._version

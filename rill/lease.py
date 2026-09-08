"""Leases and fencing tokens: a lock that survives the holder that fell asleep.

A distributed lock granted as a lease, held for a duration and
auto-released when it expires, is not safe on its own, and the
reason is the pause. A holder can acquire the lease, then stall,
a garbage-collection pause, a scheduling delay, a slow disk, long
enough that its lease expires and a second holder legitimately
acquires the lock. The first holder wakes up believing it still
holds the lock, because from inside the pause no time seemed to
pass, and writes to the shared resource that a second holder is
now also writing, and the lock protected nothing. The fencing
token closes it. Each grant carries a strictly increasing token,
and the resource remembers the highest token it has accepted and
rejects any write bearing a lower one. So when the paused holder
finally writes with its old token, the resource has already seen
the newer holder's higher token and refuses the stale write,
turning a silent double-write into a clean rejection. The lease
bounds how long a dead holder blocks others; the token is what
actually makes the lock safe against a live one that overstayed.
This module grants leases with increasing tokens and fences a
resource on the highest token, so the paused-holder corruption is
a rejected write rather than a lost update.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Halted, Invalid


@dataclass
class LeaseManager:
    lease_duration: int
    _owner: str | None = None
    _token: int = 0
    _expiry: int = 0
    _next_token: int = 1

    def __post_init__(self) -> None:
        if self.lease_duration <= 0:
            raise Invalid("lease duration must be positive")

    def acquire(self, owner: str, now: int) -> int:
        if self._owner is not None and now < self._expiry:
            raise Halted(f"lock held by {self._owner} until {self._expiry}")
        self._owner = owner
        self._token = self._next_token
        self._next_token += 1
        self._expiry = now + self.lease_duration
        return self._token


@dataclass
class FencedResource:
    _highest_token: int = 0

    def write(self, token: int, _value: str) -> None:
        if token < self._highest_token:
            raise Halted(
                f"token {token} is fenced; a holder at token "
                f"{self._highest_token} has written since"
            )
        self._highest_token = token

    def highest_token(self) -> int:
        return self._highest_token

"""Single-flight: a hot key's cache miss should fetch once, not once per caller.

When a cached key expires under load, every request that arrives
before the refresh lands sees a miss and, without coordination,
every one of them fires its own identical fetch at the upstream,
so the moment a popular key goes cold the cache turns a thousand
reads into a thousand upstream calls, the cache stampede that
takes down the very table the cache was protecting. Single-flight
collapses them. The first caller to miss a key becomes the leader
and does the one real fetch; every other caller for the same key
while that fetch is in flight is a waiter that parks on the
leader's result and issues no fetch of its own. When the leader
resolves, all the waiters get the same value from the single
call. Different keys still fetch independently, and once a key's
fetch resolves the next miss starts a fresh one, so the
collapsing is scoped to exactly the concurrent duplicates it
should remove. This module tracks the in-flight leaders and their
waiters and counts the upstream fetches, so the stampede and its
collapse are a number a test can hold.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

FETCH = "fetch"
WAIT = "wait"


@dataclass
class SingleFlight:
    _leaders: set[str] = field(default_factory=set)
    _waiters: dict[str, int] = field(default_factory=dict)
    _fetches: int = 0

    def request(self, key: str) -> str:
        if key in self._leaders:
            self._waiters[key] += 1
            return WAIT
        self._leaders.add(key)
        self._waiters[key] = 0
        self._fetches += 1
        return FETCH

    def resolve(self, key: str, _value: str) -> int:
        if key not in self._leaders:
            raise Invalid(f"{key} has no fetch in flight")
        served = self._waiters.pop(key) + 1
        self._leaders.discard(key)
        return served

    def upstream_fetches(self) -> int:
        return self._fetches

    def in_flight(self) -> list[str]:
        return sorted(self._leaders)

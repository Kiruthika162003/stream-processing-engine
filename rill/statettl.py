"""State TTL: lazy expiry keeps the clock but never reclaims a key nobody revisits.

Keyed state with a time-to-live promises that a key untouched
for longer than the TTL is gone. How gone depends on the cleanup
strategy. Lazy expiry checks the timestamp only when the key is
next accessed: cheap, no background work, but a key written once
and never read again sits in the map forever because nothing
ever comes back to notice it expired, so under churny keys the
state grows without bound even though every entry is logically
dead. Full-scan expiry sweeps the whole map on a timer and drops
everything past its TTL: it actually reclaims the memory, but it
pays a scan proportional to the live key count each sweep. This
module holds both behind one store so the difference is a call,
not a rewrite: read() honours the TTL for the caller either way,
but only sweep() shrinks the footprint, and the gap between what
read() hides and what sweep() reclaims is exactly the pile of
write-once keys that lazy expiry leaks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid, Missing


@dataclass
class TtlStore:
    ttl: int
    _written: dict[str, int] = field(default_factory=dict)
    _value: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ttl <= 0:
            raise Invalid("ttl must be positive")

    def write(self, key: str, value: str, now: int) -> None:
        self._value[key] = value
        self._written[key] = now

    def _expired(self, key: str, now: int) -> bool:
        return now - self._written[key] >= self.ttl

    def read(self, key: str, now: int) -> str:
        if key not in self._value:
            raise Missing(f"no key {key!r}")
        if self._expired(key, now):
            del self._value[key]
            del self._written[key]
            raise Missing(f"{key!r} expired under the ttl")
        return self._value[key]

    def sweep(self, now: int) -> int:
        dead = [k for k in self._value if self._expired(k, now)]
        for key in dead:
            del self._value[key]
            del self._written[key]
        return len(dead)

    def footprint(self) -> int:
        return len(self._value)

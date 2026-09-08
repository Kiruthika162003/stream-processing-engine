"""Keyed state: the memory a stream keeps, sized and accountable.

Stateless operators forget each event as it passes; everything
interesting, counts, joins, sessions, deduplication, needs
state, and state in a stream has one property batch state
never has: nobody ever tells it the input is finished, so
state that only grows is a leak with a use case. The store
keeps values per key with a last-touched clock, and expiry is
a stated policy rather than an accident of memory pressure:
keys idle past the ttl are swept, counted, and the sweep
reports the reclaimed share, because a store that cannot say
what it forgot will eventually be asked, in an incident
review, and shrug. Reads of swept keys distinguish "never
seen" from "expired", the two answers teams conflate until
the day the difference is the whole bug.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class KeyedState:
    ttl: int
    values: dict[str, int] = field(default_factory=dict)
    touched: dict[str, int] = field(default_factory=dict)
    expired_keys: set[str] = field(default_factory=set)
    swept_count: int = 0

    def __post_init__(self) -> None:
        if self.ttl <= 0:
            raise Invalid(
                "a ttl of zero keeps nothing; state without "
                "expiry is a leak with a use case"
            )

    def put(self, key: str, value: int, now: int) -> None:
        if not key:
            raise Invalid("state without a key is a global")
        self.values[key] = value
        self.touched[key] = now
        self.expired_keys.discard(key)

    def get(self, key: str) -> tuple[int | None, str]:
        if key in self.values:
            return self.values[key], "held"
        if key in self.expired_keys:
            return None, (
                "expired: was held and idled past the ttl, "
                "which is a different answer from never seen"
            )
        return None, "never seen"

    def sweep(self, now: int) -> str:
        doomed = [
            key
            for key, last in self.touched.items()
            if now - last > self.ttl
        ]
        for key in doomed:
            del self.values[key]
            del self.touched[key]
            self.expired_keys.add(key)
        self.swept_count += len(doomed)
        if not doomed:
            return (
                f"nothing idle past {self.ttl}; "
                f"{len(self.values)} key(s) working"
            )
        total_before = len(self.values) + len(doomed)
        share = 100 * len(doomed) // total_before
        return (
            f"swept {len(doomed)} key(s) ({share}% of the "
            f"store), {len(self.values)} remain; a store that "
            "cannot say what it forgot will eventually shrug "
            "in an incident review"
        )

    def census(self) -> str:
        return (
            f"{len(self.values)} live key(s), "
            f"{self.swept_count} swept over the store's life, "
            f"ttl {self.ttl}"
        )

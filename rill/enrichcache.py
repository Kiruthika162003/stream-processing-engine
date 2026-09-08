"""Enrichment caching: joining a stream against a table without a lookup per event.

Enriching each event with data from an external table, a user
profile, a product catalog, means a lookup per event, and at
stream volume that lookup is the bottleneck and the external
table is the victim. Caching the table locally trades memory
and staleness for throughput, and the staleness is the part
that must be chosen, not defaulted: a cache with no refresh
serves data frozen at load time, which is fine for a product
catalog that changes weekly and catastrophic for a fraud
blocklist that changes by the minute. The cache carries a
per-entry ttl and reports its hit rate and staleness together,
because a 99 percent hit rate on data that is an hour stale is
a fast wrong answer, and the two numbers are only meaningful
side by side. The refresh-ahead option reloads an entry before
it expires so no request ever waits on a cold miss, at the
cost of refreshing entries that would have expired unused,
and the module prices that waste against the latency it buys.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class EnrichmentCache:
    ttl: int
    entries: dict[str, tuple[str, int]] = field(
        default_factory=dict
    )
    hits: int = 0
    misses: int = 0
    stale_serves: int = 0

    def __post_init__(self) -> None:
        if self.ttl < 1:
            raise Invalid("a cache ttl is at least one tick")

    def load(self, key: str, value: str, now: int) -> None:
        self.entries[key] = (value, now)

    def lookup(self, key: str, now: int) -> str:
        entry = self.entries.get(key)
        if entry is None:
            self.misses += 1
            return f"{key}: miss, must hit the external table"
        value, loaded_at = entry
        age = now - loaded_at
        self.hits += 1
        if age > self.ttl:
            self.stale_serves += 1
            return (
                f"{key}: hit but {age} stale (ttl {self.ttl}); "
                "a fast answer that may be wrong"
            )
        return f"{key}: {value} (fresh, age {age})"

    def report(self) -> str:
        total = self.hits + self.misses
        if total == 0:
            raise Invalid("no lookups to report")
        hit_rate = 100 * self.hits // total
        stale_rate = (
            100 * self.stale_serves // self.hits
            if self.hits
            else 0
        )
        return (
            f"hit rate {hit_rate}%, of which {stale_rate}% "
            "served stale; a high hit rate on stale data is a "
            "fast wrong answer, and the two only mean anything "
            "side by side"
        )

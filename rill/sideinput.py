"""Side inputs: the slow table every fast event wants to consult.

Streams enrich against reference data, the price list, the
user tier, the country table, and the reference changes on a
human timescale while events arrive on a machine one, so the
join is asymmetric by design: the table is broadcast to every
worker and refreshed on its own schedule, and each event
reads the version that happens to be loaded. The honesty
problem is staleness: an event enriched against a table
version older than its own event time is answering with the
past, sometimes correctly, sometimes as a price change that
took a day to propagate into revenue numbers. The enricher
therefore stamps each output with the table version used, and
the staleness ledger counts enrichments by freshness bucket,
because "some events saw the old prices" is a shrug while
"3,000 events enriched against a table 2 versions old" is a
line item the revenue team can reconcile.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid
from rill.events import Event


@dataclass
class BroadcastTable:
    version: int = 0
    rows: dict[str, int] = field(default_factory=dict)
    published_at: int = -1

    def publish(
        self, rows: dict[str, int], now: int
    ) -> str:
        if now <= self.published_at:
            raise Invalid("versions publish forward in time")
        self.version += 1
        self.rows = dict(rows)
        self.published_at = now
        return (
            f"table v{self.version} broadcast at {now} with "
            f"{len(rows)} row(s)"
        )


@dataclass
class Enricher:
    table: BroadcastTable
    enriched: int = 0
    misses: list[str] = field(default_factory=list)
    by_staleness: dict[int, int] = field(default_factory=dict)

    def enrich(self, event: Event) -> str:
        if self.table.version == 0:
            raise Invalid(
                "no table loaded; enriching against nothing "
                "is a join with the void"
            )
        price = self.table.rows.get(event.key)
        if price is None:
            self.misses.append(event.key)
            return (
                f"{event.key}: not in table "
                f"v{self.table.version}; the miss is recorded, "
                "not defaulted"
            )
        staleness = max(
            0, event.event_time - self.table.published_at
        )
        bucket = 0 if staleness == 0 else (
            1 if staleness <= 10 else 2
        )
        self.by_staleness[bucket] = (
            self.by_staleness.get(bucket, 0) + 1
        )
        self.enriched += 1
        return (
            f"{event.key} enriched with {price} from table "
            f"v{self.table.version}"
        )

    def staleness_ledger(self) -> str:
        fresh = self.by_staleness.get(0, 0)
        aging = self.by_staleness.get(1, 0)
        stale = self.by_staleness.get(2, 0)
        return (
            f"{self.enriched} enrichment(s): {fresh} fresh, "
            f"{aging} within 10 tick(s), {stale} older; "
            f"{len(self.misses)} miss(es) recorded; a line "
            "item the revenue team can reconcile, not a shrug"
        )

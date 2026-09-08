from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.events import Event
from rill.sideinput import BroadcastTable, Enricher


def at(key: str, event_time: int) -> Event:
    return Event(
        key=key, value=1, event_time=event_time,
        arrival=event_time,
    )


def loaded() -> Enricher:
    table = BroadcastTable()
    table.publish({"basic": 10, "pro": 25}, now=100)
    return Enricher(table=table)


class TestTheBroadcast:
    def test_versions_publish_forward(self):
        table = BroadcastTable()
        assert table.publish({"a": 1}, now=5).startswith(
            "table v1 broadcast at 5"
        )
        with pytest.raises(Invalid):
            table.publish({"a": 2}, now=5)

    def test_enriching_against_nothing_is_refused(self):
        with pytest.raises(Invalid) as caught:
            Enricher(table=BroadcastTable()).enrich(
                at("basic", 5)
            )
        assert "join with the void" in str(caught.value)


class TestEnrichment:
    def test_the_output_names_its_table_version(self):
        enricher = loaded()
        line = enricher.enrich(at("pro", 100))
        assert line == "pro enriched with 25 from table v1"

    def test_the_miss_is_recorded_not_defaulted(self):
        enricher = loaded()
        line = enricher.enrich(at("enterprise", 100))
        assert "recorded, not defaulted" in line
        assert enricher.misses == ["enterprise"]

    def test_staleness_buckets_by_event_time_gap(self):
        enricher = loaded()
        enricher.enrich(at("basic", 100))
        enricher.enrich(at("basic", 105))
        enricher.enrich(at("pro", 150))
        ledger = enricher.staleness_ledger()
        assert ledger.startswith(
            "3 enrichment(s): 1 fresh, 1 within 10 tick(s), "
            "1 older; 0 miss(es) recorded"
        )
        assert "not a shrug" in ledger

    def test_the_refreshed_table_serves_new_prices(self):
        enricher = loaded()
        enricher.table.publish(
            {"basic": 12, "pro": 30}, now=200
        )
        line = enricher.enrich(at("basic", 205))
        assert "enriched with 12 from table v2" in line

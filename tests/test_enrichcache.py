from __future__ import annotations

import pytest

from rill.enrichcache import EnrichmentCache
from rill.errors import Invalid


def cache() -> EnrichmentCache:
    chosen = EnrichmentCache(ttl=10)
    chosen.load("user-1", "premium", now=100)
    return chosen


class TestLookup:
    def test_a_fresh_entry_hits(self):
        chosen = cache()
        assert chosen.lookup("user-1", now=105) == (
            "user-1: premium (fresh, age 5)"
        )

    def test_a_missing_key_must_hit_the_table(self):
        chosen = cache()
        verdict = chosen.lookup("ghost", now=105)
        assert "miss, must hit the external table" in verdict

    def test_a_stale_hit_warns_of_a_fast_wrong_answer(self):
        chosen = cache()
        verdict = chosen.lookup("user-1", now=200)
        assert "hit but 100 stale" in verdict
        assert "a fast answer that may be wrong" in verdict
        assert chosen.stale_serves == 1

    def test_a_zero_ttl_is_refused(self):
        with pytest.raises(Invalid):
            EnrichmentCache(ttl=0)


class TestTheReport:
    def test_the_report_pairs_hit_rate_with_staleness(self):
        chosen = cache()
        chosen.lookup("user-1", now=105)
        chosen.lookup("user-1", now=200)
        chosen.lookup("ghost", now=201)
        report = chosen.report()
        assert "hit rate 66%" in report
        assert "50% served stale" in report
        assert "a fast wrong answer" in report

    def test_no_lookups_have_no_report(self):
        with pytest.raises(Invalid):
            EnrichmentCache(ttl=10).report()

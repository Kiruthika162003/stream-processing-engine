from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.eventlint import EventLinter


def linter() -> EventLinter:
    return EventLinter(required=("event_id", "kind"))


class TestTheDoor:
    def test_the_clean_event_passes(self):
        chosen = linter()
        verdict = chosen.lint(
            "checkout-svc",
            {"event_id": "e1", "kind": "order"},
        )
        assert verdict == "checkout-svc: clean"

    def test_missing_fields_are_refused_at_the_door(self):
        chosen = linter()
        verdict = chosen.lint("legacy-svc", {"kind": "ping"})
        assert "REFUSED AT THE DOOR" in verdict
        assert "missing event_id" in verdict

    def test_the_size_budget_names_the_network_bill(self):
        chosen = linter()
        verdict = chosen.lint(
            "verbose-svc",
            {
                "event_id": "e1",
                "kind": "debug",
                "dump": "x" * 2000,
            },
        )
        assert "over the 1024 budget" in verdict
        assert "another team's network bill" in verdict

    def test_pii_travels_at_stream_speed(self):
        chosen = linter()
        verdict = chosen.lint(
            "analytics-svc",
            {
                "event_id": "e1",
                "kind": "view",
                "who": "alice@example.com",
            },
        )
        assert "PII marker in who" in verdict
        assert "compliance incident traveling" in verdict

    def test_a_ruleless_linter_is_a_doorstop(self):
        with pytest.raises(Invalid):
            EventLinter(required=())


class TestTheBill:
    def test_failures_are_billed_by_name(self):
        chosen = linter()
        chosen.lint("legacy-svc", {})
        chosen.lint("legacy-svc", {"kind": "ping"})
        chosen.lint(
            "checkout-svc", {"event_id": "e1", "kind": "o"}
        )
        bill = chosen.producer_bill()
        assert "legacy-svc: 3 failure(s)" in bill
        assert "someone else's job" in bill

    def test_the_clean_fleet_paid_its_own_hygiene(self):
        chosen = linter()
        chosen.lint(
            "checkout-svc", {"event_id": "e1", "kind": "o"}
        )
        assert "every producer paid their own hygiene" in (
            chosen.producer_bill()
        )

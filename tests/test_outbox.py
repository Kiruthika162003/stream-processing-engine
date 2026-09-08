from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.outbox import OutboxService


class TestOneCommit:
    def test_state_and_event_commit_together(self):
        service = OutboxService()
        verdict = service.place_order("ord-1", 500)
        assert "the event exists iff the write did" in verdict
        assert service.outbox == [("ord-1", "placed:500", False)]

    def test_the_rollback_leaves_no_lie(self):
        service = OutboxService()
        verdict = service.place_order(
            "ord-2", 300, crash_mid_write=True
        )
        assert "no order, no outbox row, no event, no lie" in (
            verdict
        )
        assert service.orders == {}
        assert service.outbox == []

    def test_identityless_orders_are_refused(self):
        with pytest.raises(Invalid):
            OutboxService().place_order("", 5)


class TestTheRelay:
    def test_the_relay_publishes_and_marks(self):
        service = OutboxService()
        service.place_order("ord-1", 500)
        assert service.relay_once() == (
            "ord-1 published and marked"
        )
        assert service.relay_once() == (
            "outbox drained; nothing owed"
        )

    def test_the_crash_duplicates_and_the_row_says_why(self):
        service = OutboxService()
        service.place_order("ord-1", 500)
        verdict = service.relay_once(crash_before_mark=True)
        assert "identities for the deduper" in verdict
        service.relay_once()
        assert service.published == [
            "ord-1|placed:500",
            "ord-1|placed:500",
        ]


class TestTheInvariant:
    def test_the_invariant_holds_and_measures_the_owed(self):
        service = OutboxService()
        service.place_order("ord-1", 500)
        service.place_order("ord-2", 200)
        service.relay_once()
        audit = service.invariant_audit()
        assert audit.startswith(
            "invariant holds: 2 order(s), every one with its "
            "row, 1 still owed"
        )
        assert "eventually, measured" in audit

    def test_the_bypass_is_named_dual_write(self):
        service = OutboxService()
        service.orders["sneaky"] = 99
        assert service.invariant_audit().startswith(
            "DUAL-WRITE: sneaky"
        )

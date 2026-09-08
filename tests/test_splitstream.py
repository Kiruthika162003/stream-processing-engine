from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.splitstream import StreamSplitter


def classify(event: str) -> str:
    if event.startswith("order"):
        return "orders"
    if event.startswith("refund"):
        return "refunds"
    return "unknown"


class TestRouting:
    def test_events_route_to_their_named_output(self):
        splitter = StreamSplitter(
            outputs=("orders", "refunds"), classify=classify
        )
        assert splitter.route("order-1") == "order-1 -> orders"
        assert splitter.route("refund-1") == (
            "refund-1 -> refunds"
        )

    def test_the_unmatched_event_hits_the_catch_all(self):
        splitter = StreamSplitter(
            outputs=("orders", "refunds"), classify=classify
        )
        verdict = splitter.route("weird-thing")
        assert "catch-all" in verdict
        assert "accounted, not dropped" in verdict

    def test_no_catch_all_refuses_the_silent_drop(self):
        splitter = StreamSplitter(
            outputs=("orders", "refunds"),
            classify=classify,
            has_catch_all=False,
        )
        with pytest.raises(Invalid) as caught:
            splitter.route("weird-thing")
        assert "the missing-data bug that never errors" in str(
            caught.value
        )

    def test_an_outputless_split_is_refused(self):
        with pytest.raises(Invalid):
            StreamSplitter(outputs=(), classify=classify)


class TestAccounting:
    def test_the_sum_proves_nothing_dropped(self):
        splitter = StreamSplitter(
            outputs=("orders", "refunds"), classify=classify
        )
        splitter.route("order-1")
        splitter.route("refund-1")
        splitter.route("mystery")
        accounting = splitter.accounting()
        assert "3 in, 3 out (every event accounted)" in accounting
        assert "the sum is the proof nothing dropped" in accounting

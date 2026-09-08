from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.sinkcontract import SinkContract


class TestIdempotentSinks:
    def test_a_duplicate_write_is_suppressed(self):
        sink = SinkContract(name="db", semantics="idempotent")
        sink.write("row-1", "v1")
        verdict = sink.write("row-1", "v1")
        assert "write suppressed" in verdict
        assert "honored the contract" in verdict

    def test_the_idempotent_sink_claims_exactly_once(self):
        sink = SinkContract(name="db", semantics="idempotent")
        assert sink.claims_exactly_once()

    def test_a_keyless_write_cannot_be_deduplicated(self):
        sink = SinkContract(name="db", semantics="idempotent")
        with pytest.raises(Invalid):
            sink.write("", "v")


class TestAtLeastOnceSinks:
    def test_the_duplicate_leaks_as_a_duplicate_row(self):
        sink = SinkContract(name="queue", semantics="at-least-once")
        sink.write("msg-1", "hello")
        verdict = sink.write("msg-1", "hello")
        assert "written AGAIN" in verdict
        assert "duplicate row" in verdict

    def test_it_cannot_claim_exactly_once(self):
        sink = SinkContract(name="queue", semantics="at-least-once")
        assert not sink.claims_exactly_once()
        assert "the honest component nobody asked" in (
            sink.contract_check()
        )


class TestTheContractCheck:
    def test_the_transactional_sink_holds_to_the_last_mile(self):
        sink = SinkContract(
            name="ledger", semantics="transactional"
        )
        sink.write("txn-1", "v")
        sink.write("txn-1", "v")
        check = sink.contract_check()
        assert "1 duplicate(s) suppressed" in check
        assert "holds to the last mile" in check

    def test_unknown_semantics_are_refused(self):
        with pytest.raises(Invalid):
            SinkContract(name="x", semantics="hopeful")

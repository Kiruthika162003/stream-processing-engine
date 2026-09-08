from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.ordering import OrderAuditor


class TestTheSpecies:
    def test_consecutive_sequences_are_clean(self):
        auditor = OrderAuditor()
        auditor.observe("acct-1", 0)
        assert auditor.observe("acct-1", 1) == (
            "acct-1:1 in order"
        )

    def test_the_echo_is_the_idempotence_species(self):
        auditor = OrderAuditor()
        auditor.observe("acct-1", 0)
        verdict = auditor.observe("acct-1", 0)
        assert "retry echo" in verdict
        assert auditor.echoes == ["acct-1:0"]

    def test_the_backwards_jump_is_the_dangerous_species(self):
        auditor = OrderAuditor()
        auditor.observe("acct-1", 5)
        verdict = auditor.observe("acct-1", 3)
        assert "idempotence cannot fix" in verdict
        assert "ran concurrently somewhere" in verdict
        assert auditor.reorderings == ["acct-1: 5 then 3"]

    def test_the_gap_is_a_loss_with_its_own_module(self):
        auditor = OrderAuditor()
        auditor.observe("acct-1", 0)
        verdict = auditor.observe("acct-1", 4)
        assert "skipped 3 sequence(s)" in verdict
        assert "the loss has its own module" in verdict

    def test_keys_do_not_interfere(self):
        auditor = OrderAuditor()
        auditor.observe("a", 9)
        assert "in order" in auditor.observe("b", 0)


class TestTheReport:
    def test_reorderings_carry_the_production_sentence(self):
        auditor = OrderAuditor()
        auditor.observe("acct-1", 0)
        auditor.observe("acct-1", 1)
        auditor.observe("acct-1", 1)
        auditor.observe("acct-2", 7)
        auditor.observe("acct-2", 2)
        report = auditor.species_report()
        assert report.startswith(
            "3 in order, 1 echo(es), 1 reordering(s)"
        )
        assert "balances go negative in production" in report

    def test_an_empty_audit_is_refused(self):
        with pytest.raises(Invalid):
            OrderAuditor().species_report()

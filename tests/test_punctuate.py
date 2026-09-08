from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.punctuate import PunctuatedSource


def source() -> PunctuatedSource:
    return PunctuatedSource(name="hourly-batch")


class TestTheDeclaration:
    def test_the_declaration_needs_no_margin(self):
        chosen = source()
        verdict = chosen.punctuate(through=100)
        assert "no margin to size, no straggler gamble" in (
            verdict
        )

    def test_a_retreating_promise_is_refused(self):
        chosen = source()
        chosen.punctuate(through=100)
        with pytest.raises(Invalid):
            chosen.punctuate(through=90)

    def test_events_ahead_of_the_promise_are_accepted(self):
        chosen = source()
        chosen.punctuate(through=100)
        assert chosen.event(150) == "event@150 accepted"


class TestBrokenPromises:
    def test_the_late_event_is_the_sources_fault(self):
        chosen = source()
        chosen.punctuate(through=100)
        verdict = chosen.event(90)
        assert verdict.startswith("PROMISE BROKEN")
        assert "against the source, not the pipeline" in verdict

    def test_the_clean_ledger_credits_declaration(self):
        chosen = source()
        chosen.punctuate(through=100)
        chosen.event(150)
        chosen.event(160)
        ledger = chosen.trust_ledger()
        assert "every promise kept; declared beats inferred" in (
            ledger
        )

    def test_the_lying_source_is_worse_than_a_heuristic(self):
        chosen = source()
        chosen.punctuate(through=100)
        chosen.event(150)
        chosen.event(90)
        ledger = chosen.trust_ledger()
        assert "1 broken promise(s) in 2 event(s) (50%)" in (
            ledger
        )
        assert "at least knew it was guessing" in ledger

    def test_an_eventless_source_has_no_trust(self):
        with pytest.raises(Invalid):
            source().trust_ledger()

from __future__ import annotations

import pytest

from rill.dedupe import Deduper
from rill.errors import Invalid


def deduper() -> Deduper:
    return Deduper(horizon=10)


class TestTheMemory:
    def test_the_first_offer_is_admitted(self):
        chosen = deduper()
        assert chosen.offer("evt-1", now=5)

    def test_the_replay_inside_the_horizon_is_refused(self):
        chosen = deduper()
        chosen.offer("evt-1", now=5)
        assert not chosen.offer("evt-1", now=12)
        assert chosen.refused == 1

    def test_identityless_events_cannot_repeat(self):
        with pytest.raises(Invalid):
            deduper().offer("", now=0)

    def test_a_zero_horizon_dedupes_nothing(self):
        with pytest.raises(Invalid):
            Deduper(horizon=0)


class TestTheHorizon:
    def test_the_late_replay_slips_and_is_counted(self):
        chosen = deduper()
        chosen.offer("evt-1", now=5)
        assert chosen.offer("evt-1", now=20)
        assert chosen.slipped_estimate == 1

    def test_forgetting_reclaims_the_memory(self):
        chosen = deduper()
        chosen.offer("old", now=0)
        chosen.offer("new", now=9)
        assert chosen.forget_old(now=15) == 1
        assert "old" not in chosen.seen

    def test_the_contract_states_both_clauses(self):
        chosen = deduper()
        chosen.offer("evt-1", now=5)
        chosen.offer("evt-1", now=7)
        chosen.offer("evt-1", now=20)
        contract = chosen.contract()
        assert contract.startswith(
            "exactly once, within a horizon of 10: 2 admitted, "
            "1 replay(s) refused, 1 known slip(s)"
        )
        assert "honest half of the product" in contract
